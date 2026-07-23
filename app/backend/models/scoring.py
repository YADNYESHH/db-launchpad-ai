from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .enums import ConfidenceBand, PriorityBand


class DriverScore(BaseModel):
    driver_name: str
    weight: float  # out of 100, sums to 100 within a sub-score
    raw_score: float  # 0-100, the driver's own evaluation
    weighted_score: float  # raw_score * weight / 100
    rationale: str
    missing_data: bool = False


class SubScore(BaseModel):
    sub_score_type: str
    score_value: float  # 0-100
    weight_config_version: str
    driver_scores: list[DriverScore]
    top_drivers: list[str]
    missing_data_flags: list[str] = Field(default_factory=list)
    confidence_band: ConfidenceBand
    rationale: str


class ScoreRecord(BaseModel):
    startup_id: str
    sub_scores: list[SubScore]
    final_score: float
    priority_band: PriorityBand
    weight_config_version: str
    missing_data_flags: list[str] = Field(default_factory=list)
    threshold_detail: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
