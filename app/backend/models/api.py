"""Request/response wrapper models used only by the FastAPI layer (main.py) —
kept separate from the domain models in this package's other modules."""

from pydantic import BaseModel

from .enums import ApprovalStatus
from .profile import ExpansionSignal, PainPointProfile, PaymentProfile, StartupProfile
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


class GenerateRecommendationRequest(BaseModel):
    startup_id: str
    force: bool = False


class DecideRecommendationRequest(BaseModel):
    decision: ApprovalStatus  # must be approved | revised | rejected


class ProposeWeightConfigRequest(BaseModel):
    sub_score_driver_tables: dict[str, list[DriverWeight]] | None = None
    final_rollup_weights: dict[str, float] | None = None
    change_reason: str
