from ..models.recommendation import BANNED_PHRASES


def scan_for_banned_phrases(text: str) -> list[str]:
    """Doc §23.4 'what not to claim' / §24.4 conduct guardrails: scan any
    LLM-generated (or template) text for language that would turn decision
    support into an implied guarantee, suitability statement, or regulated
    advice. Returns the list of matched phrases (empty = clean)."""
    lowered = text.lower()
    return [phrase for phrase in BANNED_PHRASES if phrase in lowered]
