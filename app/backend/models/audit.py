from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    audit_id: str
    startup_id: str
    event_type: str  # profile_created | score_calculated | recommendation_generated |
    # recommendation_approved | recommendation_rejected | weight_config_changed
    payload: dict = Field(default_factory=dict)
    actor: str  # user_id, or "system"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
