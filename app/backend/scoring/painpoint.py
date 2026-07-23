"""Client Pain-Point Intensity driver functions (doc pp. 20-21)."""
from .context import ScoringContext, DriverResult, clamp

_MAX_RECONCILIATION_HOURS_WEEKLY = 20
_MAX_FAILED_PAYMENTS_MONTHLY = 20


def payment_delay_impact(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    score = 30 if ctx.pain.payment_delay_issue else 10
    score += clamp(ctx.pain.failed_payment_count_monthly / _MAX_FAILED_PAYMENTS_MONTHLY * 70)
    return DriverResult(
        clamp(score),
        f"payment_delay_issue={ctx.pain.payment_delay_issue}, "
        f"{ctx.pain.failed_payment_count_monthly} failed payments/month.",
    )


def cash_visibility_pain(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    score = 50 if ctx.pain.cash_visibility_gap else 15
    score += min(ctx.pain.number_of_providers, 4) * 10
    return DriverResult(
        clamp(score),
        f"cash_visibility_gap={ctx.pain.cash_visibility_gap}, "
        f"{ctx.pain.number_of_providers} banking providers in use.",
    )


def reconciliation_burden(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    hours = ctx.pain.reconciliation_effort_hours_weekly
    score = clamp(hours / _MAX_RECONCILIATION_HOURS_WEEKLY * 100)
    return DriverResult(score, f"{hours:.1f} hours/week spent on manual reconciliation.")


def cost_and_fee_pressure(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    score = 75 if ctx.pain.cost_pressure else 25
    return DriverResult(score, f"cost_pressure={ctx.pain.cost_pressure}.")


def operational_scalability_constraint(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain or not ctx.payment:
        return DriverResult(0, "Payment or pain-point profile missing.", missing_data=True)
    # High transaction growth combined with many manual providers/accounts signals a
    # process that will not scale without automation.
    score = ctx.payment.expected_growth_rate * 100 + ctx.pain.number_of_bank_accounts * 5
    return DriverResult(
        clamp(score),
        f"Growth rate {ctx.payment.expected_growth_rate:.0%} against "
        f"{ctx.pain.number_of_bank_accounts} manually-managed accounts.",
    )


def board_or_cfo_urgency(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    score = 70 if ctx.pain.cfo_urgency else 25
    months = ctx.profile.expansion_timeline_months
    if months is not None and months <= 6:
        score += 20
    return DriverResult(
        clamp(score),
        f"cfo_urgency={ctx.pain.cfo_urgency}; expansion in "
        f"{months if months is not None else 'unknown'} months.",
    )


def risk_of_client_churn_or_provider_switch(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    score = 80 if ctx.pain.provider_switch_risk else 20
    return DriverResult(score, f"provider_switch_risk={ctx.pain.provider_switch_risk}.")


DRIVER_FUNCTIONS = {
    "payment_delay_impact": payment_delay_impact,
    "cash_visibility_pain": cash_visibility_pain,
    "reconciliation_burden": reconciliation_burden,
    "cost_and_fee_pressure": cost_and_fee_pressure,
    "operational_scalability_constraint": operational_scalability_constraint,
    "board_or_cfo_urgency": board_or_cfo_urgency,
    "risk_of_client_churn_or_provider_switch": risk_of_client_churn_or_provider_switch,
}
