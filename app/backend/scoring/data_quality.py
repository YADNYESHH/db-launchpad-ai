"""Data Availability & Explainability driver functions (doc pp. 18-19)."""
from .context import DriverResult, ScoringContext, clamp


def source_reliability(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    weights = [1.0 if s.source_type.value == "synthetic" else 0.8 for s in ctx.signals]
    score = sum(weights) / len(weights) * 100
    return DriverResult(clamp(score), f"{len(ctx.signals)} signals; source reliability weighted by source type.")


def completeness_of_required_fields(ctx: ScoringContext) -> DriverResult:
    present = [ctx.payment is not None, ctx.pain is not None, len(ctx.signals) > 0]
    score = sum(present) / len(present) * 100
    return DriverResult(score, f"{sum(present)}/3 required data groups present (payment, pain-point, signals).")


def consistency_across_signals(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    countries_in_signals = {s.country for s in ctx.signals if s.country}
    target = set(ctx.profile.target_countries)
    if not countries_in_signals:
        return DriverResult(50, "No country-specific signals to cross-check against target markets.")
    consistent = countries_in_signals.issubset(target)
    score = 90 if consistent else 40
    return DriverResult(score, f"Signal countries {countries_in_signals} vs target markets {target}.")


def evidence_traceability(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    traceable = [bool(s.source_label) and bool(s.evidence_note) for s in ctx.signals]
    score = sum(traceable) / len(traceable) * 100
    return DriverResult(score, f"{sum(traceable)}/{len(traceable)} signals have full source label + evidence note.")


def freshness_of_data(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    ref_date = ctx.profile.created_at.date()
    ages = [(ref_date - s.signal_date).days for s in ctx.signals]
    avg_age = sum(ages) / len(ages)
    score = clamp(100 - avg_age)
    return DriverResult(score, f"Average signal age {avg_age:.0f} days relative to profile creation.")


def explainability_of_score_drivers(ctx: ScoringContext) -> DriverResult:
    return DriverResult(
        90,
        "Structural guarantee: every driver in every sub-score always returns a rationale string (doc: "
        "'no score displayed without an explanation').",
    )


def permission_and_governance_readiness(ctx: ScoringContext) -> DriverResult:
    score = 95 if ctx.profile.synthetic_flag else 55
    return DriverResult(score, f"synthetic_flag={ctx.profile.synthetic_flag}.")


DRIVER_FUNCTIONS = {
    "source_reliability": source_reliability,
    "completeness_of_required_fields": completeness_of_required_fields,
    "consistency_across_signals": consistency_across_signals,
    "evidence_traceability": evidence_traceability,
    "freshness_of_data": freshness_of_data,
    "explainability_of_score_drivers": explainability_of_score_drivers,
    "permission_and_governance_readiness": permission_and_governance_readiness,
}
