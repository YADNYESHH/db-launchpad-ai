import pytest

from ..scoring import ScoringContext
from ..seed.data import (
    DEFAULT_WEIGHT_CONFIG,
    NOVATRADE_PAIN_POINT_PROFILE,
    NOVATRADE_PAYMENT_PROFILE,
    NOVATRADE_PROFILE,
    NOVATRADE_SIGNALS,
)


@pytest.fixture
def novatrade_ctx() -> ScoringContext:
    return ScoringContext(
        profile=NOVATRADE_PROFILE,
        weight_config=DEFAULT_WEIGHT_CONFIG,
        payment=NOVATRADE_PAYMENT_PROFILE,
        pain=NOVATRADE_PAIN_POINT_PROFILE,
        signals=list(NOVATRADE_SIGNALS),
    )


@pytest.fixture
def empty_ctx() -> ScoringContext:
    return ScoringContext(
        profile=NOVATRADE_PROFILE,
        weight_config=DEFAULT_WEIGHT_CONFIG,
        payment=None,
        pain=None,
        signals=[],
    )
