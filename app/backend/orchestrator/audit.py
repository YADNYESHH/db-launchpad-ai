import uuid
from datetime import datetime, timezone

from ..models import AuditEvent
from ..store import Store


def log_event(store: Store, startup_id: str, event_type: str, payload: dict, actor: str) -> AuditEvent:
    event = AuditEvent(
        audit_id=str(uuid.uuid4()),
        startup_id=startup_id,
        event_type=event_type,
        payload=payload,
        actor=actor,
        timestamp=datetime.now(timezone.utc),
    )
    store.append_audit_event(event)
    return event
