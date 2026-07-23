from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .enums import ApprovalStatus, PriorityBand

# doc §23.4: "what not to claim" — fixed, non-negotiable disclaimers on every brief.
STANDARD_NON_CLAIMS = [
    "Do not state or imply guaranteed savings or revenue.",
    "Do not state or imply credit approval or eligibility.",
    "Do not state a product is suitable for this client.",
    "Do not provide regulated financial, investment, or tax advice.",
]

# Banned-phrase guardrail used by the Trust & Control stage (llm/guardrails.py).
BANNED_PHRASES = [
    "guaranteed", "guarantee", "will save you", "risk-free", "approved for credit",
    "credit approval", "suitable for you", "suitable for this client", "we recommend you invest",
    "financial advice", "investment advice", "definitely will", "certain to",
]


class RecommendationRecord(BaseModel):
    recommendation_id: str
    startup_id: str
    score_record_id: str
    final_score: float
    priority_band: PriorityBand
    client_summary: str
    why_now: str
    top_drivers: list[str]
    missing_drivers: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    product_themes: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    what_not_to_claim: list[str] = Field(default_factory=lambda: list(STANDARD_NON_CLAIMS))
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    llm_used: bool = False
    guardrail_flags: list[str] = Field(default_factory=list)
