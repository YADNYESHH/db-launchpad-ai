"""RM Actionability driver functions (doc pp. 19-20)."""
from .context import ScoringContext, DriverResult, clamp


def clarity_of_next_best_action(ctx: ScoringContext) -> DriverResult:
    score = 90 if (ctx.payment and ctx.pain) else 40
    return DriverResult(score, "Concrete next action requires both payment and pain-point data.")


def quality_of_conversation_prompts(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    flags = [
        ctx.pain.payment_delay_issue,
        ctx.pain.cash_visibility_gap,
        ctx.pain.cost_pressure,
        ctx.pain.cfo_urgency,
    ]
    score = sum(flags) * 25
    return DriverResult(clamp(score), f"{sum(flags)}/4 pain-point themes available to build questions from.")


def product_conversation_readiness(ctx: ScoringContext) -> DriverResult:
    score = 85 if ctx.payment else 30
    return DriverResult(score, "Payment/currency data available to ground product themes." if ctx.payment else "No payment data.")


def timing_urgency_for_outreach(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    months = ctx.profile.expansion_timeline_months
    score = 40
    if ctx.pain.cfo_urgency:
        score += 30
    if months is not None and months <= 6:
        score += 30
    return DriverResult(clamp(score), f"cfo_urgency={ctx.pain.cfo_urgency}, timeline={months} months.")


def evidence_confidence_for_rm_trust(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal evidence available.", missing_data=True)
    avg_conf = sum(s.confidence for s in ctx.signals) / len(ctx.signals)
    return DriverResult(clamp(avg_conf * 100), f"Average signal confidence {avg_conf:.2f} across {len(ctx.signals)} signals.")


def workflow_integration_potential(ctx: ScoringContext) -> DriverResult:
    return DriverResult(80, "Recommendation is surfaced directly in the RM dashboard's approval queue.")


def action_outcome_measurability(ctx: ScoringContext) -> DriverResult:
    return DriverResult(80, "Every approval/rejection/reject decision is captured in the audit log for later calibration.")


DRIVER_FUNCTIONS = {
    "clarity_of_next_best_action": clarity_of_next_best_action,
    "quality_of_conversation_prompts": quality_of_conversation_prompts,
    "product_conversation_readiness": product_conversation_readiness,
    "timing_urgency_for_outreach": timing_urgency_for_outreach,
    "evidence_confidence_for_rm_trust": evidence_confidence_for_rm_trust,
    "workflow_integration_potential": workflow_integration_potential,
    "action_outcome_measurability": action_outcome_measurability,
}
