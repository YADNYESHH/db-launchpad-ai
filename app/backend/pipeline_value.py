"""Indicative pipeline-value estimation.

Estimates the *indicative* annual banking revenue a bank could earn from a
startup, derived purely from public/estimated figures (annual revenue and
annual cross-border payment value) plus a probability weighting based on the
startup's priority band.

This is NOT a promise or commitment of revenue - it is a rough, deterministic
estimate meant to help rank and prioritize pipeline opportunities.
"""

from pydantic import BaseModel

# 40 bps blended FX + payment margin applied to cross-border payment value.
_PAYMENTS_FX_FEE_RATE = 0.004

# 10 bps cash-management / product fee applied to cross-border payment value.
_CASH_MGMT_FEE_RATE = 0.001

# Assumed operating balance held as deposits, as a fraction of annual revenue.
_DEPOSIT_BALANCE_RATE = 0.06

# Assumed net interest margin earned on the deposit balance.
_DEPOSIT_NIM_RATE = 0.025

# Probability-weighting multiplier applied to the total, by priority band.
_BAND_MULTIPLIERS: dict[str | None, float] = {
    "high_priority": 1.0,
    "monitor": 0.7,
    "validate": 0.5,
    "no_immediate_action": 0.3,
    None: 0.6,
}

BASIS = (
    "Indicative estimate from public/estimated figures, probability-weighted "
    "by priority band. Not a revenue commitment."
)


class PipelineValue(BaseModel):
    estimated_annual_bank_revenue_eur: float
    breakdown: dict[str, float]  # component -> eur
    basis: str  # short human note that this is indicative


def estimate_pipeline_value(
    annual_revenue_eur: float,
    annual_cross_border_payment_value_eur: float | None,
    priority_band: str | None,
) -> PipelineValue:
    """Estimate indicative annual bank revenue from a startup.

    Deterministic, pure function based solely on public/estimated inputs.
    The result is an indicative estimate only, never a revenue commitment.
    """
    cross_border_value = annual_cross_border_payment_value_eur or 0

    payments_fx_fees = cross_border_value * _PAYMENTS_FX_FEE_RATE
    cash_mgmt_fees = cross_border_value * _CASH_MGMT_FEE_RATE
    deposit_nii = annual_revenue_eur * _DEPOSIT_BALANCE_RATE * _DEPOSIT_NIM_RATE

    band_multiplier = _BAND_MULTIPLIERS.get(priority_band, _BAND_MULTIPLIERS[None])

    total = (payments_fx_fees + cash_mgmt_fees + deposit_nii) * band_multiplier

    breakdown = {
        "payments_fx_fees": round(payments_fx_fees),
        "cash_management_fees": round(cash_mgmt_fees),
        "deposit_net_interest": round(deposit_nii),
        "band_probability_multiplier": band_multiplier,
    }

    return PipelineValue(
        estimated_annual_bank_revenue_eur=round(total),
        breakdown=breakdown,
        basis=BASIS,
    )
