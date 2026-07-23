import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from .auth.deps import get_current_user, require_roles
from .auth.security import TokenPayload, create_access_token, verify_password
from .models import ApprovalStatus, Role, UserPublic
from .models.api import (
    CreateProfileRequest,
    DecideRecommendationRequest,
    GenerateRecommendationRequest,
    ProfileBundle,
    ProposeWeightConfigRequest,
)
from .orchestrator import NotFoundError, decide_recommendation, ensure_weight_config, run_recommendation, run_scoring
from .orchestrator.audit import log_event
from .seed.data import DEFAULT_WEIGHT_CONFIG, DEMO_USERS
from .seed.data import (
    NOVATRADE_ID,
    NOVATRADE_PAIN_POINT_PROFILE,
    NOVATRADE_PAYMENT_PROFILE,
    NOVATRADE_PROFILE,
    NOVATRADE_SIGNALS,
)
from .store import get_store

logger = logging.getLogger(__name__)


def _seed_if_empty() -> None:
    store = get_store()
    if store.get_profile(NOVATRADE_ID) is None:
        store.save_profile(NOVATRADE_PROFILE)
        store.save_payment_profile(NOVATRADE_PAYMENT_PROFILE)
        store.save_pain_point_profile(NOVATRADE_PAIN_POINT_PROFILE)
        store.save_signals(NOVATRADE_ID, NOVATRADE_SIGNALS)
        logger.info("Seeded synthetic NovaTrade AI GmbH profile.")
    if store.get_active_weight_config() is None:
        store.save_weight_config(DEFAULT_WEIGHT_CONFIG)
        logger.info("Seeded default weight config v1.")
    for user in DEMO_USERS:
        if store.get_user_by_email(user.email) is None:
            store.save_user(user)
    logger.info("Seeded %d demo users.", len(DEMO_USERS))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_if_empty()
    yield


app = FastAPI(title="LaunchPad AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo/hackathon scope; tighten before any real production use
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    # Not served at /healthz: that exact path was observed to be intercepted
    # ahead of this app (a Google-branded 404, not ours) on this project's
    # Cloud Run *.run.app domain, while every other path routes correctly.
    return {"status": "healthy", "service": "launchpad-ai", "synthetic_only": True}


# ---------------------------------------------------------------- auth -----
@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    store = get_store()
    user = store.get_user_by_email(form.username)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "user": UserPublic(**user.model_dump())}


@app.get("/auth/me", response_model=UserPublic)
def me(current: TokenPayload = Depends(get_current_user)):
    return UserPublic(user_id=current.user_id, email=current.email, name=current.name, role=current.role)


# ------------------------------------------------------------ profiles -----
@app.post("/profiles", status_code=status.HTTP_201_CREATED)
def create_profile(
    req: CreateProfileRequest,
    current: TokenPayload = Depends(require_roles(Role.RM, Role.PRODUCT_OWNER)),
):
    store = get_store()
    store.save_profile(req.profile)
    if req.payment:
        store.save_payment_profile(req.payment)
    if req.pain:
        store.save_pain_point_profile(req.pain)
    if req.signals:
        store.save_signals(req.profile.startup_id, req.signals)

    log_event(store, req.profile.startup_id, "profile_created", payload={"synthetic_flag": req.profile.synthetic_flag}, actor=current.user_id)
    return {
        "startup_id": req.profile.startup_id,
        "validation_status": "valid",
        "synthetic_flag": req.profile.synthetic_flag,
    }


@app.get("/profiles", response_model=list[ProfileBundle])
def list_profiles(current: TokenPayload = Depends(get_current_user)):
    store = get_store()
    return [
        ProfileBundle(
            profile=p,
            payment=store.get_payment_profile(p.startup_id),
            pain=store.get_pain_point_profile(p.startup_id),
            signals=store.get_signals(p.startup_id),
        )
        for p in store.list_profiles()
    ]


@app.get("/profiles/{startup_id}", response_model=ProfileBundle)
def get_profile(startup_id: str, current: TokenPayload = Depends(get_current_user)):
    store = get_store()
    profile = store.get_profile(startup_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No profile found for startup_id={startup_id}")
    return ProfileBundle(
        profile=profile,
        payment=store.get_payment_profile(startup_id),
        pain=store.get_pain_point_profile(startup_id),
        signals=store.get_signals(startup_id),
    )


@app.post("/profiles/{startup_id}/score")
def score_profile(startup_id: str, current: TokenPayload = Depends(get_current_user)):
    store = get_store()
    try:
        score_id, record = run_scoring(store, startup_id, actor=current.user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"score_id": score_id, "score_record": record}


# ------------------------------------------------------- recommendations ---
@app.post("/recommendations/generate")
def generate_recommendation_endpoint(
    req: GenerateRecommendationRequest,
    current: TokenPayload = Depends(require_roles(Role.RM, Role.PRODUCT_OWNER)),
):
    store = get_store()
    try:
        recommendation, reason = run_recommendation(store, req.startup_id, actor=current.user_id, force=req.force)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if recommendation is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=reason)
    return recommendation


@app.post("/recommendations/{recommendation_id}/approve")
def approve_recommendation_endpoint(
    recommendation_id: str,
    req: DecideRecommendationRequest,
    current: TokenPayload = Depends(require_roles(Role.RM)),
):
    store = get_store()
    try:
        rec = decide_recommendation(store, recommendation_id, actor=current.user_id, decision=req.decision)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return rec


@app.get("/recommendations/{recommendation_id}")
def get_recommendation_endpoint(recommendation_id: str, current: TokenPayload = Depends(get_current_user)):
    store = get_store()
    rec = store.get_recommendation(recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"No recommendation found for id={recommendation_id}")
    return rec


# --------------------------------------------------------------- audit -----
@app.get("/audit/{startup_id}")
def get_audit_trail(startup_id: str, current: TokenPayload = Depends(require_roles(Role.CONTROL_REVIEWER, Role.RM, Role.PRODUCT_OWNER))):
    store = get_store()
    return store.get_audit_trail(startup_id)


# ------------------------------------------------------------- weights -----
@app.get("/weights")
def get_active_weights(current: TokenPayload = Depends(get_current_user)):
    store = get_store()
    config = ensure_weight_config(store)
    return config


@app.get("/weights/all")
def list_all_weights(current: TokenPayload = Depends(require_roles(Role.PRODUCT_OWNER, Role.CONTROL_REVIEWER))):
    store = get_store()
    return store.list_weight_configs()


@app.post("/weights/propose", status_code=status.HTTP_201_CREATED)
def propose_weights(
    req: ProposeWeightConfigRequest,
    current: TokenPayload = Depends(require_roles(Role.PRODUCT_OWNER)),
):
    from .models.weights import WeightConfig

    store = get_store()
    active = ensure_weight_config(store)
    new_version = f"v{len(store.list_weight_configs()) + 1}"
    proposed = WeightConfig(
        version_id=new_version,
        owner=current.user_id,
        active=False,
        change_reason=req.change_reason,
        sub_score_driver_tables=req.sub_score_driver_tables or active.sub_score_driver_tables,
        final_rollup_weights=req.final_rollup_weights or active.final_rollup_weights,
    )
    store.save_weight_config(proposed)
    log_event(store, "system", "weight_config_proposed", payload={"version_id": new_version, "reason": req.change_reason}, actor=current.user_id)
    return proposed


@app.post("/weights/{version_id}/activate")
def activate_weights(version_id: str, current: TokenPayload = Depends(require_roles(Role.ADMIN))):
    store = get_store()
    target = None
    for config in store.list_weight_configs():
        if config.version_id == version_id:
            target = config
        if config.active:
            config.active = False
            store.save_weight_config(config)
    if target is None:
        raise HTTPException(status_code=404, detail=f"No weight config found for version_id={version_id}")
    target.active = True
    target.approved_date = datetime.now(timezone.utc)
    store.save_weight_config(target)
    log_event(store, "system", "weight_config_changed", payload={"version_id": version_id, "activated_by": current.user_id}, actor=current.user_id)
    return target


# ----------------------------------------------------------- static SPA ----
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
