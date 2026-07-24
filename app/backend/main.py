import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from .auth.deps import get_current_user, require_roles
from .auth.security import TokenPayload, create_access_token, verify_password
from .discovery.agent import diagnose_discovery
from .discovery.seed_live import seed_live_portfolio
from .models import Role, UserPublic
from .models.api import (
    CreateProfileRequest,
    DecideRecommendationRequest,
    DiscoveryRequest,
    GenerateRecommendationRequest,
    ProfileBundle,
    ProposeWeightConfigRequest,
)
from .orchestrator import (
    NotFoundError,
    decide_recommendation,
    ensure_weight_config,
    run_discovery,
    run_recommendation,
    run_scoring,
)
from .orchestrator.audit import log_event
from .orchestrator.validation import find_duplicate_profile
from .pipeline_value import estimate_pipeline_value
from .scoring import ScoringContext, compute_decathlon
from .seed.data import (
    DEFAULT_WEIGHT_CONFIG,
    DEMO_USERS,
    SEED_PROFILES,
)
from .store import get_store

logger = logging.getLogger(__name__)


def _seed_if_empty() -> None:
    store = get_store()
    for profile, payment, pain, signals in SEED_PROFILES:
        if store.get_profile(profile.startup_id) is None:
            store.save_profile(profile)
            store.save_payment_profile(payment)
            store.save_pain_point_profile(pain)
            store.save_signals(profile.startup_id, signals)
            logger.info("Seeded synthetic profile %s (%s).", profile.startup_id, profile.name)
    if store.get_active_weight_config() is None:
        store.save_weight_config(DEFAULT_WEIGHT_CONFIG)
        logger.info("Seeded default weight config v1.")
    for user in DEMO_USERS:
        if store.get_user_by_email(user.email) is None:
            store.save_user(user)
    logger.info("Seeded %d demo users.", len(DEMO_USERS))

    for profile in store.list_profiles():
        if store.get_latest_score_record(profile.startup_id) is None:
            try:
                run_scoring(store, profile.startup_id, actor="system")
            except Exception:
                logger.exception("Failed to auto-score profile %s", profile.startup_id)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


def _startup_seed() -> None:
    """Seed the store on startup.

    Default (LIVE_SEED unset): synthetic seed only — unchanged behavior.

    LIVE_SEED truthy: attempt a live-first seed of REAL startups via grounded
    discovery. If it adds nothing (e.g. no GCP creds), fall back to the
    synthetic seed so the app always has data. The synthetic fallback is never
    weakened; a live seed only *adds* real companies on top of demo users and
    weight config.
    """
    if not _truthy(os.getenv("LIVE_SEED")):
        _seed_if_empty()
        return

    store = get_store()
    # Ensure demo users / weight config / auto-scoring baseline always exists,
    # regardless of whether the live call succeeds.
    _seed_if_empty()
    try:
        result = seed_live_portfolio(store, actor="system")
    except Exception:
        logger.exception("Live portfolio seed failed; synthetic seed retained.")
        return
    if result.get("added", 0) > 0:
        logger.info(
            "Live-seeded %d real startups across sectors %s.",
            result["added"],
            result.get("sectors"),
        )
    else:
        logger.warning(
            "Live seed added no startups (%s); retaining synthetic seed.",
            result.get("reasons"),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _startup_seed()
    yield


app = FastAPI(title="LaunchPad AI", version="1.0.0", lifespan=lifespan)

# The deployed app serves its frontend from the same origin as its API, so
# browser-based use in production never needs cross-origin access at all.
# CORS is only for local development (Vite dev server on a different port)
# and any explicitly deployed frontend origins - never a bare wildcard.
_DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", _DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    # Not served at /healthz: that exact path was observed to be intercepted
    # ahead of this app (a Google-branded 404, not ours) on this project's
    # Cloud Run *.run.app domain, while every other path routes correctly.
    return {
        "status": "healthy",
        "service": "launchpad-ai",
        "synthetic_only": True,
        "version": os.getenv("BUILD_SHA", "dev"),
    }


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

    duplicate = find_duplicate_profile(store.list_profiles(), req.profile)
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A profile named '{duplicate.name}' in {duplicate.hq_country} already exists "
                f"as startup_id={duplicate.startup_id}. Use that profile instead of creating a duplicate."
            ),
        )

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


def _build_bundle(store, profile) -> ProfileBundle:
    latest = store.get_latest_score_record(profile.startup_id)
    payment = store.get_payment_profile(profile.startup_id)
    pain = store.get_pain_point_profile(profile.startup_id)
    signals = store.get_signals(profile.startup_id)
    ctx = ScoringContext(
        profile=profile,
        weight_config=ensure_weight_config(store),
        payment=payment,
        pain=pain,
        signals=signals,
    )
    score = latest[1] if latest else None
    pipeline_value = estimate_pipeline_value(
        annual_revenue_eur=profile.annual_revenue_eur,
        annual_cross_border_payment_value_eur=(
            payment.annual_cross_border_payment_value_eur if payment else None
        ),
        priority_band=score.priority_band.value if score else None,
    )
    return ProfileBundle(
        profile=profile,
        payment=payment,
        pain=pain,
        signals=signals,
        score=score,
        decathlon=compute_decathlon(ctx),
        pipeline_value=pipeline_value,
    )


@app.get("/profiles", response_model=list[ProfileBundle])
def list_profiles(current: TokenPayload = Depends(get_current_user)):
    store = get_store()
    bundles = [_build_bundle(store, p) for p in store.list_profiles()]
    # Ranked: scored startups first (highest score first), unscored after.
    return sorted(bundles, key=lambda b: b.score.final_score if b.score else -1, reverse=True)


@app.get("/profiles/{startup_id}", response_model=ProfileBundle)
def get_profile(startup_id: str, current: TokenPayload = Depends(get_current_user)):
    store = get_store()
    profile = store.get_profile(startup_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No profile found for startup_id={startup_id}")
    return _build_bundle(store, profile)


@app.get("/portfolio/summary")
def portfolio_summary(current: TokenPayload = Depends(get_current_user)):
    """Deterministic roll-up of indicative pipeline value across all profiles."""
    store = get_store()
    bundles = [_build_bundle(store, p) for p in store.list_profiles()]

    total_pipeline_value_eur = 0.0
    band_counts: dict[str, int] = {}
    scored_count = 0
    for bundle in bundles:
        if bundle.pipeline_value is not None:
            total_pipeline_value_eur += bundle.pipeline_value.estimated_annual_bank_revenue_eur
        if bundle.score is not None:
            scored_count += 1
            band_key = bundle.score.priority_band.value
        else:
            band_key = "unscored"
        band_counts[band_key] = band_counts.get(band_key, 0) + 1

    return {
        "total_pipeline_value_eur": total_pipeline_value_eur,
        "band_counts": band_counts,
        "scored_count": scored_count,
        "total_count": len(bundles),
    }


# ------------------------------------------------------------ discovery -----
@app.post("/discovery/search")
def discovery_search(
    req: DiscoveryRequest,
    current: TokenPayload = Depends(require_roles(Role.RM, Role.PRODUCT_OWNER)),
):
    """Live-discover real startups for a sector via grounded search, score
    them, and return a ranked summary. Degrades gracefully if grounding is
    unavailable (returns reason, keeps the synthetic seed intact)."""
    store = get_store()
    limit = max(1, min(req.limit, 6))
    return run_discovery(store, req.sector, actor=current.user_id, limit=limit)


@app.post("/discovery/seed-portfolio")
def seed_portfolio_endpoint(
    body: dict | None = Body(default=None),
    current: TokenPayload = Depends(require_roles(Role.RM, Role.PRODUCT_OWNER, Role.ADMIN)),
):
    """Live-first: populate the portfolio with REAL startups across several
    sectors via grounded discovery. Fully defensive — a failing sector never
    aborts the rest, and if the live layer is unavailable the response simply
    reports ``live=false`` with reasons (the synthetic seed stays intact)."""
    store = get_store()
    body = body or {}
    sectors = body.get("sectors")
    per_sector = body.get("per_sector", 3)
    try:
        per_sector = int(per_sector)
    except (TypeError, ValueError):
        per_sector = 3
    result = seed_live_portfolio(store, actor=current.user_id, sectors=sectors, per_sector=per_sector)
    return {**result, "total_profiles": len(store.list_profiles())}



@app.get("/discovery/diagnostics")
def discovery_diagnostics(
    current: TokenPayload = Depends(require_roles(Role.ADMIN)),
):
    """Admin-only: run ONE real grounded generation and return a structured,
    SAFE diagnostic that surfaces the real error (type + truncated message) or
    the region that succeeded. Lets an admin see why live discovery is failing
    in production without swallowing the error. Never raises; leaks no creds."""
    return diagnose_discovery()


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
def list_all_weights(current: TokenPayload = Depends(require_roles(Role.PRODUCT_OWNER, Role.CONTROL_REVIEWER, Role.ADMIN))):
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
