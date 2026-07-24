"""Recommendation stage (doc §23.4 RM Brief Output Template) + Trust & Control
guardrails. This is the ONLY stage that may call the LLM, and only to
rephrase prose sections — never to alter the score, band, or approval logic.
"""
import uuid
from datetime import datetime, timezone

from ..llm.guardrails import scan_for_banned_phrases
from ..llm.vertex_client import generate_narrative
from ..models import (
    ApprovalStatus,
    ConfidenceBand,
    ExpansionSignal,
    PainPointProfile,
    PaymentProfile,
    PriorityBand,
    RecommendationRecord,
    ScoreRecord,
    StartupProfile,
)
from .validation import (
    check_data_freshness,
    check_source_credibility,
    find_duplicate_signals,
    validate_recommendation_output,
)

_PRODUCT_THEMES_BY_FLAG = {
    "payment_delay_issue": ["Payment tracking and status visibility"],
    "cash_visibility_gap": ["Cash visibility dashboard", "Virtual accounts"],
    "cost_pressure": ["FX exposure review", "Pricing transparency on cross-border fees"],
    "provider_switch_risk": ["Primary operating account migration"],
}

_DEFAULT_PRODUCT_THEMES = ["Multi-currency accounts", "Cross-border collections", "Reconciliation automation"]


def _build_client_summary(profile: StartupProfile, payment: PaymentProfile | None) -> str:
    countries = ", ".join(profile.target_countries) if profile.target_countries else "new markets"
    payment_line = (
        f" It processes an estimated EUR {payment.annual_cross_border_payment_value_eur:,.0f} "
        f"in cross-border payments annually."
        if payment
        else ""
    )
    return (
        f"{profile.name} is a {profile.growth_stage.lower()} in {profile.sector}, headquartered in "
        f"{profile.hq_country}, expanding into {countries}.{payment_line}"
    )


def _build_why_now(profile: StartupProfile, signals: list[ExpansionSignal]) -> str:
    if not signals:
        return f"{profile.name} has an expansion plan on file but no corroborating signals yet."
    highlights = "; ".join(f"{s.signal_type.replace('_', ' ')} ({s.country or 'n/a'})" for s in signals[:3])
    months = profile.expansion_timeline_months
    timing = f" with go-live expected in {months} months" if months is not None else ""
    return f"Recent signals indicate active expansion{timing}: {highlights}."


def _build_suggested_questions(pain: PainPointProfile | None) -> list[str]:
    questions = [
        "Which countries and currencies will your first cross-border invoices be issued in?",
        "How are you currently tracking payment status across your banking providers?",
        "What does your reconciliation process look like today, and where does it break down?",
    ]
    if pain:
        if pain.cash_visibility_gap:
            questions.append("How much visibility do you have into consolidated cash position across accounts?")
        if pain.cost_pressure:
            questions.append("What FX margin or fee levels are you seeing on your current cross-border payments?")
        if pain.provider_switch_risk:
            questions.append("Would you consider consolidating onto a single primary operating bank?")
    questions.append("What is your target go-live date for the new market, and what would you need from a bank by then?")
    return questions[:7]


def _build_product_themes(pain: PainPointProfile | None) -> list[str]:
    themes: list[str] = []
    if pain:
        for flag_name, flag_themes in _PRODUCT_THEMES_BY_FLAG.items():
            if getattr(pain, flag_name, False):
                themes.extend(flag_themes)
    for theme in _DEFAULT_PRODUCT_THEMES:
        if theme not in themes:
            themes.append(theme)
    return themes


def _build_caveats(score_record: ScoreRecord, signals: list[ExpansionSignal]) -> list[str]:
    caveats = []
    if score_record.missing_data_flags:
        caveats.append(f"Missing or incomplete data for: {', '.join(score_record.missing_data_flags)}.")
    weakest = min(score_record.sub_scores, key=lambda s: s.score_value)
    if weakest.score_value < 60:
        label = weakest.sub_score_type.replace("_", " ").title()
        caveats.append(
            f"{label} is comparatively weak ({weakest.score_value:.0f}/100) and should be validated with the client."
        )

    # Self-validation performed by this stage before handing the brief to an
    # RM: source credibility, freshness, and duplicate/redundant evidence.
    credibility_issue = check_source_credibility(signals)
    if credibility_issue:
        caveats.append(credibility_issue)
    freshness_issue = check_data_freshness(signals, as_of=datetime.now(timezone.utc).date())
    if freshness_issue:
        caveats.append(freshness_issue)
    caveats.extend(find_duplicate_signals(signals))

    caveats.append("All data used is synthetic and has not been validated against real client records.")
    return caveats


def _determine_evidence_confidence(
    score_record: ScoreRecord, signals: list[ExpansionSignal]
) -> ConfidenceBand:
    """Rolls up evidence quality into one exec-facing confidence band,
    combining the data-quality sub-score's own confidence with the
    source-credibility and freshness checks performed above."""
    data_quality = next(
        (s for s in score_record.sub_scores if s.sub_score_type == "data_availability_explainability"), None
    )
    if data_quality is not None and data_quality.confidence_band == ConfidenceBand.LOW:
        return ConfidenceBand.LOW
    if check_source_credibility(signals) or check_data_freshness(signals, as_of=datetime.now(timezone.utc).date()):
        return ConfidenceBand.LOW
    if data_quality is not None and data_quality.confidence_band == ConfidenceBand.MEDIUM:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.HIGH


def generate_recommendation(
    profile: StartupProfile,
    score_record: ScoreRecord,
    score_record_id: str,
    payment: PaymentProfile | None,
    pain: PainPointProfile | None,
    signals: list[ExpansionSignal],
    force: bool = False,
) -> tuple[RecommendationRecord | None, str | None]:
    """Returns (recommendation, rejection_reason). doc §15.1D: a brief is only
    generated when the opportunity meets the High-priority rule, or the RM
    explicitly requests a draft for review (force=True)."""
    if score_record.priority_band != PriorityBand.HIGH_PRIORITY and not force:
        return None, (
            f"Priority band is '{score_record.priority_band.value}', not high_priority. "
            "Pass force=True to generate a draft anyway for RM review."
        )

    top_drivers = sorted(score_record.sub_scores, key=lambda s: s.score_value, reverse=True)[:3]
    weak_drivers = sorted(score_record.sub_scores, key=lambda s: s.score_value)[:3]

    client_summary = _build_client_summary(profile, payment)
    why_now = _build_why_now(profile, signals)

    # Attempt LLM rephrasing of the two prose sections only; template stays authoritative.
    llm_used = False
    prompt = (
        "Rewrite the following two short business summaries in clear, professional, factual prose "
        "for an internal relationship-manager briefing at a bank. Do not add any claims, numbers, "
        "or facts that are not already present. Do not state guarantees, suitability, or advice. "
        "Return exactly two paragraphs separated by a blank line, in the same order.\n\n"
        f"1) Client summary: {client_summary}\n\n2) Why now: {why_now}"
    )
    narrative, used = generate_narrative(prompt)
    if used and narrative:
        parts = [p.strip() for p in narrative.split("\n\n") if p.strip()]
        if len(parts) >= 2:
            candidate_summary, candidate_why_now = parts[0], parts[1]
            flags = scan_for_banned_phrases(candidate_summary) + scan_for_banned_phrases(candidate_why_now)
            if not flags:
                client_summary, why_now = candidate_summary, candidate_why_now
                llm_used = True

    guardrail_flags = scan_for_banned_phrases(client_summary) + scan_for_banned_phrases(why_now)
    if guardrail_flags:
        # Should be unreachable given the check above, but never ship flagged text.
        client_summary = _build_client_summary(profile, payment)
        why_now = _build_why_now(profile, signals)
        llm_used = False

    approval_status = (
        ApprovalStatus.DRAFT
        if score_record.priority_band == PriorityBand.HIGH_PRIORITY
        else ApprovalStatus.VALIDATION_REQUIRED
    )

    recommendation = RecommendationRecord(
        recommendation_id=str(uuid.uuid4()),
        startup_id=profile.startup_id,
        score_record_id=score_record_id,
        final_score=score_record.final_score,
        priority_band=score_record.priority_band,
        client_summary=client_summary,
        why_now=why_now,
        top_drivers=[d.sub_score_type for d in top_drivers],
        missing_drivers=[d.sub_score_type for d in weak_drivers if d.score_value < 60],
        evidence_used=[
            f"{s.source_label} ({s.signal_date.isoformat()}, confidence {s.confidence:.2f})" for s in signals
        ],
        suggested_questions=_build_suggested_questions(pain),
        product_themes=_build_product_themes(pain),
        caveats=_build_caveats(score_record, signals),
        approval_status=approval_status,
        generated_at=datetime.now(timezone.utc),
        llm_used=llm_used,
        guardrail_flags=guardrail_flags,
        evidence_confidence=_determine_evidence_confidence(score_record, signals),
    )

    # Output validation: this stage never hands off an incomplete brief. If a
    # problem is found (should be unreachable given the construction above,
    # but defended anyway), the brief is force-downgraded to
    # validation_required rather than silently released as a draft.
    problems = validate_recommendation_output(recommendation)
    if problems:
        recommendation.approval_status = ApprovalStatus.VALIDATION_REQUIRED
        recommendation.validation_notes = problems

    return recommendation, None
