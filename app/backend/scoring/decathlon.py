"""The 10-dimension Decathlon digital twin (doc §10, pp. 29-30).

Distinct from the 7 cross-border *opportunity* sub-scores in rollup.py: the
Decathlon is the company's current-state maturity across ten business
dimensions - the "digital twin backbone" the document describes. It is
deterministic, derived from the same profile/payment/pain/signal data, and
carries a top-driver rationale per dimension so nothing is unexplained.

These scores describe the company; the opportunity scorecard decides the
banking action. Both are shown side by side in the dashboard.
"""
from pydantic import BaseModel

from .context import ScoringContext, clamp

DECATHLON_DIMENSIONS = [
    ("growth_velocity", "Growth velocity"),
    ("funding_and_capital", "Funding & capital"),
    ("cross_border_expansion", "Cross-border expansion"),
    ("treasury_and_liquidity", "Treasury & liquidity"),
    ("fx_exposure", "FX exposure"),
    ("payments_and_collections", "Payments & collections"),
    ("financing_and_credit", "Financing & credit"),
    ("regulatory_and_compliance", "Regulatory & compliance"),
    ("payroll_and_workforce", "Payroll & workforce"),
    ("investor_and_ipo_readiness", "Investor & IPO readiness"),
]

_FUNDING_STAGE_SCORE = {
    "seed": 30, "series a": 50, "series b": 68, "series c": 82,
    "series d": 90, "growth": 85, "scaleup": 80,
}
_GROWTH_STAGE_SCORE = {
    "early-stage": 30, "seed": 35, "growth": 70, "scaleup": 80, "series a": 55,
    "series b": 72, "series c": 85,
}


class DecathlonDimension(BaseModel):
    key: str
    label: str
    score: float
    top_driver: str


class DecathlonTwin(BaseModel):
    dimensions: list[DecathlonDimension]


def _fx_score(ctx: ScoringContext) -> tuple[float, str]:
    n_foreign = len(ctx.foreign_currencies)
    score = clamp(n_foreign * 25 + 10)
    return score, f"{n_foreign} foreign currencies in use"


def _payments_score(ctx: ScoringContext) -> tuple[float, str]:
    if not ctx.payment:
        return 0.0, "no payment data"
    score = clamp(ctx.total_monthly_payments / 5)
    return score, f"{ctx.total_monthly_payments} monthly payments"


def _cross_border_score(ctx: ScoringContext) -> tuple[float, str]:
    n = len(ctx.profile.target_countries) + len(ctx.profile.current_countries)
    score = clamp(n * 18)
    return score, f"{len(ctx.profile.target_countries)} target markets"


def _treasury_score(ctx: ScoringContext) -> tuple[float, str]:
    if not ctx.pain:
        return 40.0, "limited treasury data"
    score = clamp(40 + ctx.pain.number_of_bank_accounts * 10 + (20 if ctx.pain.cash_visibility_gap else 0))
    return score, f"{ctx.pain.number_of_bank_accounts} bank accounts"


def _growth_score(ctx: ScoringContext) -> tuple[float, str]:
    base = _GROWTH_STAGE_SCORE.get(ctx.profile.growth_stage.lower(), 55)
    if ctx.payment and ctx.payment.expected_growth_rate:
        base = clamp(base + ctx.payment.expected_growth_rate * 60)
    return clamp(base), f"{ctx.profile.growth_stage}"


def _funding_score(ctx: ScoringContext) -> tuple[float, str]:
    return clamp(_FUNDING_STAGE_SCORE.get(ctx.profile.funding_stage.lower(), 45)), f"{ctx.profile.funding_stage}"


def _financing_score(ctx: ScoringContext) -> tuple[float, str]:
    if not ctx.pain:
        return 45.0, "limited data"
    score = clamp(35 + (25 if ctx.pain.cost_pressure else 0) + (20 if ctx.pain.cfo_urgency else 0))
    return score, "working-capital pressure" if ctx.pain.cost_pressure else "stable cash position"


def _regulatory_score(ctx: ScoringContext) -> tuple[float, str]:
    n = len(ctx.profile.target_countries)
    score = clamp(45 + n * 12)
    return score, f"{n} new jurisdictions" if n else "single jurisdiction"


def _payroll_score(ctx: ScoringContext) -> tuple[float, str]:
    hiring = len(ctx.signals_of_type("international_hiring"))
    score = clamp(35 + hiring * 25 + len(ctx.profile.current_countries) * 5)
    return score, f"{hiring} international-hiring signals" if hiring else "domestic workforce"


def _investor_score(ctx: ScoringContext) -> tuple[float, str]:
    base = _FUNDING_STAGE_SCORE.get(ctx.profile.funding_stage.lower(), 40)
    # Later-stage funding implies closer to investor/IPO readiness.
    score = clamp(base - 10)
    return score, f"{ctx.profile.funding_stage} stage"


_DIMENSION_FUNCS = {
    "growth_velocity": _growth_score,
    "funding_and_capital": _funding_score,
    "cross_border_expansion": _cross_border_score,
    "treasury_and_liquidity": _treasury_score,
    "fx_exposure": _fx_score,
    "payments_and_collections": _payments_score,
    "financing_and_credit": _financing_score,
    "regulatory_and_compliance": _regulatory_score,
    "payroll_and_workforce": _payroll_score,
    "investor_and_ipo_readiness": _investor_score,
}


def compute_decathlon(ctx: ScoringContext) -> DecathlonTwin:
    dims = []
    for key, label in DECATHLON_DIMENSIONS:
        score, driver = _DIMENSION_FUNCS[key](ctx)
        dims.append(DecathlonDimension(key=key, label=label, score=round(score, 1), top_driver=driver))
    return DecathlonTwin(dimensions=dims)
