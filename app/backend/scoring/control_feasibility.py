"""Control & Implementation Feasibility driver functions.

This 5-driver table is our documented gap-fill for a sub-score the concept
document names and weights (§21, §23.3) but does not publish a full 100-point
breakdown for — see the header comment in models/weights.py.
"""
from .context import ScoringContext, DriverResult, clamp

_RECOGNISED_JURISDICTIONS = {
    "germany", "austria", "netherlands", "singapore", "united kingdom",
    "france", "ireland", "luxembourg", "spain", "italy", "sweden", "denmark",
}


def kyc_and_onboarding_feasibility(ctx: ScoringContext) -> DriverResult:
    countries = {c.lower() for c in ([ctx.profile.hq_country] + ctx.profile.target_countries)}
    unrecognised = countries - _RECOGNISED_JURISDICTIONS
    score = 85 if not unrecognised else 50
    return DriverResult(score, f"Unrecognised jurisdictions for KYC playbook: {unrecognised or 'none'}.")


def data_permission_and_classification_readiness(ctx: ScoringContext) -> DriverResult:
    score = 95 if ctx.profile.synthetic_flag else 55
    return DriverResult(score, f"synthetic_flag={ctx.profile.synthetic_flag} simplifies data-permission review.")


def product_suitability_and_approval_readiness(ctx: ScoringContext) -> DriverResult:
    score = 85 if ctx.payment else 40
    return DriverResult(score, "Payment profile lets the RM map to an approved cross-border product theme." if ctx.payment else "No payment profile.")


def human_approval_workflow_readiness(ctx: ScoringContext) -> DriverResult:
    return DriverResult(
        100,
        "Structural guarantee: the RM-approval gate is enforced in code for every recommendation "
        "(doc: 'no client-facing summary without approval') — always ready.",
    )


def operational_delivery_complexity(ctx: ScoringContext) -> DriverResult:
    if not ctx.pain:
        return DriverResult(0, "No pain-point profile on file.", missing_data=True)
    score = 100 - min(ctx.pain.number_of_bank_accounts * 8, 50) - min(ctx.pain.number_of_providers * 5, 20)
    return DriverResult(
        clamp(score),
        f"{ctx.pain.number_of_bank_accounts} accounts across {ctx.pain.number_of_providers} providers to reconcile.",
    )


DRIVER_FUNCTIONS = {
    "kyc_and_onboarding_feasibility": kyc_and_onboarding_feasibility,
    "data_permission_and_classification_readiness": data_permission_and_classification_readiness,
    "product_suitability_and_approval_readiness": product_suitability_and_approval_readiness,
    "human_approval_workflow_readiness": human_approval_workflow_readiness,
    "operational_delivery_complexity": operational_delivery_complexity,
}
