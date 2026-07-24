"""Self-validation helpers used BY the existing pipeline stages (profile
ingestion and recommendation generation) rather than by a separate
compliance/governance/risk agent. Every business stage is responsible for
validating its own inputs and outputs before handing off to the next one.
"""
from datetime import date

from ..models.profile import ExpansionSignal, StartupProfile
from ..models.recommendation import RecommendationRecord


def find_duplicate_profile(
    existing_profiles: list[StartupProfile], candidate: StartupProfile
) -> StartupProfile | None:
    """Duplicate detection for the profile-ingestion stage: the same real
    company entering under a second startup_id. Matched on normalized name +
    HQ country, since startup_id is caller-assigned and carries no
    real-world uniqueness guarantee."""
    for existing in existing_profiles:
        if existing.startup_id == candidate.startup_id:
            continue
        if (
            existing.name.strip().lower() == candidate.name.strip().lower()
            and existing.hq_country.strip().lower() == candidate.hq_country.strip().lower()
        ):
            return existing
    return None


def find_duplicate_signals(signals: list[ExpansionSignal]) -> list[str]:
    """Duplicate/redundant evidence detection: the same (signal_type, country,
    evidence_note) reported more than once would silently inflate a startup's
    apparent evidence base. Returns human-readable descriptions of any
    duplicates found."""
    seen: dict[tuple, str] = {}
    duplicates: list[str] = []
    for s in signals:
        key = (s.signal_type, s.country, s.evidence_note.strip().lower())
        if key in seen:
            duplicates.append(f"Duplicate signal: '{s.signal_type}' for {s.country} appears more than once ({s.signal_id} vs {seen[key]}).")
        else:
            seen[key] = s.signal_id
    return duplicates


# Evidence older than this is flagged as stale rather than silently trusted.
_STALE_SIGNAL_AGE_DAYS = 180
# Below this average source-confidence, evidence is flagged as low-credibility.
_LOW_CREDIBILITY_THRESHOLD = 0.6


def check_source_credibility(signals: list[ExpansionSignal]) -> str | None:
    """Source-credibility validation: don't silently trust evidence that is
    low-confidence or entirely single-source."""
    if not signals:
        return None
    avg_confidence = sum(s.confidence for s in signals) / len(signals)
    if avg_confidence < _LOW_CREDIBILITY_THRESHOLD:
        return (
            f"Evidence source credibility is low (average confidence {avg_confidence:.2f}); "
            "corroborate with an additional source before acting on this alone."
        )
    return None


def check_data_freshness(signals: list[ExpansionSignal], as_of: date) -> str | None:
    """Freshness validation: evidence that is old relative to `as_of` (the
    date the recommendation is being generated) should not be presented as
    current without a caveat."""
    if not signals:
        return None
    ages = [(as_of - s.signal_date).days for s in signals]
    avg_age = sum(ages) / len(ages)
    if avg_age > _STALE_SIGNAL_AGE_DAYS:
        return f"Evidence is stale (average age {avg_age:.0f} days); refresh signals before relying on this brief."
    return None


REQUIRED_NON_EMPTY_FIELDS = (
    "client_summary",
    "why_now",
    "top_drivers",
    "suggested_questions",
    "product_themes",
    "what_not_to_claim",
)


def validate_recommendation_output(rec: RecommendationRecord) -> list[str]:
    """Output validation for the recommendation stage: never return or
    persist a brief that is missing a field a Relationship Manager depends
    on. Returns a list of problems (empty = valid)."""
    problems = []
    for field_name in REQUIRED_NON_EMPTY_FIELDS:
        value = getattr(rec, field_name)
        if not value:
            problems.append(f"Recommendation is missing required field '{field_name}'.")
    if not (0 <= rec.final_score <= 100):
        problems.append(f"final_score {rec.final_score} is out of the valid 0-100 range.")
    return problems
