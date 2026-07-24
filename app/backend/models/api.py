"""Request/response wrapper models used only by the FastAPI layer (main.py) —
kept separate from the domain models in this package's other modules."""

from pydantic import BaseModel

from ..pipeline_value import PipelineValue
from ..scoring.decathlon import DecathlonTwin
from .enums import ApprovalStatus
from .profile import ExpansionSignal, PainPointProfile, PaymentProfile, StartupProfile
from .scoring import ScoreRecord
from .weights import DriverWeight


class CreateProfileRequest(BaseModel):
    profile: StartupProfile
    payment: PaymentProfile | None = None
    pain: PainPointProfile | None = None
    signals: list[ExpansionSignal] = []


class ProfileBundle(BaseModel):
    profile: StartupProfile
    payment: PaymentProfile | None = None
    pain: PainPointProfile | None = None
    signals: list[ExpansionSignal] = []
    # Latest score for this startup, if it has been scored. Lets the portfolio
    # view rank startups without a second round-trip per card.
    score: ScoreRecord | None = None
    # 10-dimension Decathlon digital-twin maturity view (current-state, distinct
    # from the opportunity score).
    decathlon: DecathlonTwin | None = None
    # Indicative annual bank revenue estimate for this startup (never a
    # commitment). Present whenever the profile can be estimated.
    pipeline_value: PipelineValue | None = None


class DiscoveryRequest(BaseModel):
    sector: str
    limit: int = 4


class GenerateRecommendationRequest(BaseModel):
    startup_id: str
    force: bool = False


class DecideRecommendationRequest(BaseModel):
    decision: ApprovalStatus  # must be approved | revised | rejected


class ProposeWeightConfigRequest(BaseModel):
    sub_score_driver_tables: dict[str, list[DriverWeight]] | None = None
    final_rollup_weights: dict[str, float] | None = None
    change_reason: str
