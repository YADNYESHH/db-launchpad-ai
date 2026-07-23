"""Request/response wrapper models used only by the FastAPI layer (main.py) —
kept separate from the domain models in this package's other modules."""
from typing import Optional

from pydantic import BaseModel

from .enums import ApprovalStatus
from .profile import ExpansionSignal, PainPointProfile, PaymentProfile, StartupProfile


class CreateProfileRequest(BaseModel):
    profile: StartupProfile
    payment: Optional[PaymentProfile] = None
    pain: Optional[PainPointProfile] = None
    signals: list[ExpansionSignal] = []


class ProfileBundle(BaseModel):
    profile: StartupProfile
    payment: Optional[PaymentProfile] = None
    pain: Optional[PainPointProfile] = None
    signals: list[ExpansionSignal] = []


class GenerateRecommendationRequest(BaseModel):
    startup_id: str
    force: bool = False


class DecideRecommendationRequest(BaseModel):
    decision: ApprovalStatus  # must be approved | revised | rejected


class ProposeWeightConfigRequest(BaseModel):
    sub_score_driver_tables: Optional[dict[str, list[tuple[str, float]]]] = None
    final_rollup_weights: Optional[dict[str, float]] = None
    change_reason: str
