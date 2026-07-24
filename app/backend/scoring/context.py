from dataclasses import dataclass, field

from ..models.profile import (
    ExpansionSignal,
    PainPointProfile,
    PaymentProfile,
    StartupProfile,
)
from ..models.weights import WeightConfig


@dataclass
class ScoringContext:
    """Everything a driver function needs to compute its raw 0-100 score.

    `payment` and `pain` are Optional because a profile can, in principle, be
    scored before its payment/pain-point data is entered — in which case every
    driver that depends on the missing object must report `missing_data=True`
    rather than silently defaulting to 0 (doc §23.9 / §15.1B: missing mandatory
    data must never be silently treated as zero).
    """

    profile: StartupProfile
    weight_config: WeightConfig
    payment: PaymentProfile | None = None
    pain: PainPointProfile | None = None
    signals: list[ExpansionSignal] = field(default_factory=list)

    @property
    def home_currency(self) -> str:
        return "EUR"

    @property
    def foreign_currencies(self) -> list[str]:
        if not self.payment:
            return []
        return [c for c in self.payment.currencies if c != self.home_currency]

    @property
    def total_monthly_payments(self) -> int:
        if not self.payment:
            return 0
        return self.payment.monthly_payment_count_inbound + self.payment.monthly_payment_count_outbound

    def signals_of_type(self, signal_type: str) -> list[ExpansionSignal]:
        return [s for s in self.signals if s.signal_type == signal_type]


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


@dataclass
class DriverResult:
    raw_score: float
    rationale: str
    missing_data: bool = False

