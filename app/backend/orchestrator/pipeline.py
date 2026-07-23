"""Wires the 7-stage pipeline together against a Store. Every stage's
output is persisted and every transition is audited (doc: "log inputs,
generated outputs, approval status, and timestamps" — 100% of events)."""
import uuid
from datetime import datetime, timezone

from ..models import ApprovalStatus, RecommendationRecord, ScoreRecord
from ..models.weights import default_weight_config
from ..scoring import ScoringContext, score_startup
from ..store import Store
from .audit import log_event
from .recommend import generate_recommendation


class NotFoundError(Exception):
    pass


def ensure_weight_config(store: Store):
    config = store.get_active_weight_config()
    if config is None:
        config = default_weight_config(version_id="v1", owner="system")
        store.save_weight_config(config)
    return config


def run_scoring(store: Store, startup_id: str, actor: str) -> tuple[str, ScoreRecord]:
    profile = store.get_profile(startup_id)
    if profile is None:
        raise NotFoundError(f"No profile found for startup_id={startup_id}")

    weight_config = ensure_weight_config(store)
    ctx = ScoringContext(
        profile=profile,
        weight_config=weight_config,
        payment=store.get_payment_profile(startup_id),
        pain=store.get_pain_point_profile(startup_id),
        signals=store.get_signals(startup_id),
    )
    record = score_startup(ctx)
    score_id = str(uuid.uuid4())
    store.save_score_record(record, score_id)

    log_event(
        store,
        startup_id,
        "score_calculated",
        payload={
            "score_id": score_id,
            "final_score": record.final_score,
            "priority_band": record.priority_band.value,
            "weight_config_version": record.weight_config_version,
            "missing_data_flags": record.missing_data_flags,
        },
        actor=actor,
    )
    return score_id, record


def run_recommendation(
    store: Store, startup_id: str, actor: str, force: bool = False
) -> tuple[RecommendationRecord | None, str | None]:
    profile = store.get_profile(startup_id)
    if profile is None:
        raise NotFoundError(f"No profile found for startup_id={startup_id}")

    latest = store.get_latest_score_record(startup_id)
    if latest is None:
        raise NotFoundError(f"No score record found for startup_id={startup_id}; call POST /profiles/{{id}}/score first")
    score_id, score_record = latest

    recommendation, reason = generate_recommendation(
        profile=profile,
        score_record=score_record,
        score_record_id=score_id,
        payment=store.get_payment_profile(startup_id),
        pain=store.get_pain_point_profile(startup_id),
        signals=store.get_signals(startup_id),
        force=force,
    )

    if recommendation is None:
        log_event(
            store, startup_id, "recommendation_blocked", payload={"reason": reason, "score_id": score_id}, actor=actor
        )
        return None, reason

    store.save_recommendation(recommendation)
    log_event(
        store,
        startup_id,
        "recommendation_generated",
        payload={
            "recommendation_id": recommendation.recommendation_id,
            "approval_status": recommendation.approval_status.value,
            "llm_used": recommendation.llm_used,
            "guardrail_flags": recommendation.guardrail_flags,
        },
        actor=actor,
    )
    return recommendation, None


def decide_recommendation(
    store: Store, recommendation_id: str, actor: str, decision: ApprovalStatus
) -> RecommendationRecord:
    """decision must be one of APPROVED, REVISED, REJECTED — never DRAFT or
    VALIDATION_REQUIRED (those are system-set states, not human decisions)."""
    if decision not in (ApprovalStatus.APPROVED, ApprovalStatus.REVISED, ApprovalStatus.REJECTED):
        raise ValueError(f"Invalid human decision: {decision}")

    rec = store.get_recommendation(recommendation_id)
    if rec is None:
        raise NotFoundError(f"No recommendation found for recommendation_id={recommendation_id}")

    rec.approval_status = decision
    rec.approver = actor
    rec.approved_at = datetime.now(timezone.utc)
    store.save_recommendation(rec)

    log_event(
        store,
        rec.startup_id,
        f"recommendation_{decision.value}",
        payload={"recommendation_id": recommendation_id, "approver": actor},
        actor=actor,
    )
    return rec
