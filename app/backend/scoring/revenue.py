"""Revenue Potential driver functions (doc pp. 14-15, weights in
models/weights.py::REVENUE_POTENTIAL_DRIVERS).

The document specifies *what* each driver should assess and the qualitative
direction of the scoring logic (e.g. "higher payment value increases fee and
relationship potential") but not exact formulas or benchmark thresholds. The
benchmarks below are our documented, deterministic, versioned assumption —
calibratable later using RM feedback and conversion outcomes, per the
document's own Recommendation 7 ("use RM feedback ... to calibrate weights
over time"). They are pure functions of `ctx`: identical input always yields
an identical score.
"""
from .context import DriverResult, ScoringContext, clamp

# Benchmark ceilings (score reaches 100 at or above these values), calibrated
# to the document's explicitly targeted segment — "SME, MidCap and scaleup"
# (§4, §5) — not large multinational corporates. A scaleup moving EUR 8M/yr
# cross-border, or carrying EUR 30M/yr revenue, is already at the top of this
# segment's range.
_MAX_ANNUAL_PAYMENT_VALUE_EUR = 8_000_000
_MAX_MONTHLY_PAYMENT_COUNT = 500
_MAX_ANNUAL_REVENUE_EUR = 30_000_000


def estimated_annual_cross_border_payment_value(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(0, "No payment profile on file.", missing_data=True)
    value = ctx.payment.annual_cross_border_payment_value_eur
    score = clamp(value / _MAX_ANNUAL_PAYMENT_VALUE_EUR * 100)
    return DriverResult(score, f"EUR {value:,.0f} annual cross-border payment value.")


def payment_frequency_and_repeatability(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(0, "No payment profile on file.", missing_data=True)
    count = ctx.total_monthly_payments
    score = clamp(count / _MAX_MONTHLY_PAYMENT_COUNT * 100)
    return DriverResult(score, f"{count} recurring cross-border payments per month.")


def operating_account_stickiness(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(0, "No payment profile on file.", missing_data=True)
    provider = (ctx.payment.current_payment_provider or "").lower()
    if provider == "bank":
        return DriverResult(80, "Already primary-bank-served; strong stickiness upside.")
    if provider == "fintech":
        return DriverResult(55, "Currently served by a fintech, not a bank; displaceable but not yet won.")
    return DriverResult(40, "No established payment provider identified yet.")


def deposit_and_liquidity_value(ctx: ScoringContext) -> DriverResult:
    revenue = ctx.profile.annual_revenue_eur
    score = clamp(revenue / _MAX_ANNUAL_REVENUE_EUR * 100)
    return DriverResult(score, f"EUR {revenue:,.0f} annual revenue used as a deposit-value proxy.")


def cash_management_product_attach_rate(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    score = 40 + min(ctx.pain.number_of_bank_accounts, 5) * 10
    if ctx.pain.cash_visibility_gap:
        score += 20
    return DriverResult(
        clamp(score),
        f"{ctx.pain.number_of_bank_accounts} bank accounts; cash visibility gap="
        f"{ctx.pain.cash_visibility_gap}.",
    )


def fx_adjacency_from_payment_corridors(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(0, "No payment profile on file.", missing_data=True)
    n_currencies = len(ctx.foreign_currencies)
    n_corridors = len(ctx.payment.payment_corridors)
    score = n_currencies * 25 + n_corridors * 10
    return DriverResult(
        clamp(score),
        f"{n_currencies} foreign currencies across {n_corridors} payment corridors.",
    )


def trade_and_working_capital_adjacency(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(0, "No payment profile on file.", missing_data=True)
    score = ctx.payment.expected_growth_rate * 200
    return DriverResult(
        clamp(score),
        f"Expected payment volume growth rate of {ctx.payment.expected_growth_rate:.0%}.",
    )


def client_growth_velocity(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(0, "No payment profile on file.", missing_data=True)
    score = ctx.payment.expected_growth_rate * 150
    months = ctx.profile.expansion_timeline_months
    if months is not None and months <= 6:
        score += 30
    return DriverResult(
        clamp(score),
        f"Growth rate {ctx.payment.expected_growth_rate:.0%}; expansion timeline "
        f"{months if months is not None else 'unknown'} months.",
    )


def competitive_displacement_risk(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment or not ctx.pain:
        return DriverResult(0, "Payment or pain-point profile missing.", missing_data=True)
    provider = (ctx.payment.current_payment_provider or "").lower()
    score = 40
    if provider == "fintech":
        score += 30
    if ctx.pain.provider_switch_risk:
        score += 25
    return DriverResult(
        clamp(score),
        f"Current provider='{provider}'; provider_switch_risk={ctx.pain.provider_switch_risk}.",
    )


def implementation_feasibility(ctx: ScoringContext) -> DriverResult:
    have_payment = ctx.payment is not None
    have_pain = ctx.pain is not None
    completeness = sum([have_payment, have_pain]) / 2
    score = 50 + completeness * 40
    return DriverResult(
        clamp(score),
        f"Profile data completeness: payment={have_payment}, pain_point={have_pain}.",
    )


DRIVER_FUNCTIONS = {
    "estimated_annual_cross_border_payment_value": estimated_annual_cross_border_payment_value,
    "payment_frequency_and_repeatability": payment_frequency_and_repeatability,
    "operating_account_stickiness": operating_account_stickiness,
    "deposit_and_liquidity_value": deposit_and_liquidity_value,
    "cash_management_product_attach_rate": cash_management_product_attach_rate,
    "fx_adjacency_from_payment_corridors": fx_adjacency_from_payment_corridors,
    "trade_and_working_capital_adjacency": trade_and_working_capital_adjacency,
    "client_growth_velocity": client_growth_velocity,
    "competitive_displacement_risk": competitive_displacement_risk,
    "implementation_feasibility": implementation_feasibility,
}
