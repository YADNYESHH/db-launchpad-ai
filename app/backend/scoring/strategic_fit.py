"""Strategic Fit driver functions (doc pp. 16-17)."""
from .context import DriverResult, ScoringContext, clamp


def corporate_bank_product_depth(ctx: ScoringContext) -> DriverResult:
    score = 85 if ctx.payment else 50
    return DriverResult(score, "Cross-border payments/collections/cash-management is a core Corporate Bank capability.")


def global_hausbank_alignment(ctx: ScoringContext) -> DriverResult:
    n = len(ctx.profile.target_countries)
    score = clamp(n * 35 + 15)
    return DriverResult(score, f"{n} target countries requiring multi-country banking coverage.")


def sme_midcap_scaleup_relevance(ctx: ScoringContext) -> DriverResult:
    priority_stages = {"scaleup", "sme", "midcap", "growth"}
    score = 90 if ctx.profile.growth_stage.lower() in priority_stages else 55
    return DriverResult(score, f"Growth stage='{ctx.profile.growth_stage}'.")


def payments_scale_and_platform_strategy_fit(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(0, "No payment profile on file.", missing_data=True)
    score = clamp(ctx.total_monthly_payments / 400 * 100)
    return DriverResult(score, f"{ctx.total_monthly_payments} monthly payments to scale onto bank rails.")


def cross_divisional_monetisation_potential(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    signals = [len(ctx.foreign_currencies) > 0, ctx.pain.cost_pressure, ctx.pain.cash_visibility_gap]
    score = 30 + sum(signals) * 23
    return DriverResult(clamp(score), "FX/treasury/cash-management adjacency signal count: " f"{sum(signals)}/3.")


def coverage_model_fit(ctx: ScoringContext) -> DriverResult:
    return DriverResult(80, "Release 1 model assumes every scored startup has an assigned RM owner.")


def brand_and_relationship_advantage(ctx: ScoringContext) -> DriverResult:
    if not ctx.payment:
        return DriverResult(40, "No current payment provider on file.")
    provider = (ctx.payment.current_payment_provider or "").lower()
    score = {"fintech": 70, "bank": 50, "none": 40}.get(provider, 40)
    return DriverResult(score, f"Current provider='{provider}'.")


DRIVER_FUNCTIONS = {
    "corporate_bank_product_depth": corporate_bank_product_depth,
    "global_hausbank_alignment": global_hausbank_alignment,
    "sme_midcap_scaleup_relevance": sme_midcap_scaleup_relevance,
    "payments_scale_and_platform_strategy_fit": payments_scale_and_platform_strategy_fit,
    "cross_divisional_monetisation_potential": cross_divisional_monetisation_potential,
    "coverage_model_fit": coverage_model_fit,
    "brand_and_relationship_advantage": brand_and_relationship_advantage,
}
