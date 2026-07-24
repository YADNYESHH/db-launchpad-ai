"""RM doubt-resolution chat: a Relationship Manager asks a free-text question
about one startup and gets an answer grounded in what the system already
knows, with an optional live-verified lookup for anything not already on
file. Every exchange is persisted immediately (auto-save) and logged to the
same audit trail every other stage uses - this is not a separate subsystem,
it is one more self-validating capability on the existing pipeline.
"""
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    message_id: str
    startup_id: str
    role: Literal["rm", "assistant"]
    text: str
    # Real source URLs when the assistant's answer used a live-grounded lookup;
    # empty when the answer was built purely from existing on-file data.
    citations: list[str] = Field(default_factory=list)
    llm_used: bool = False
    guardrail_flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
