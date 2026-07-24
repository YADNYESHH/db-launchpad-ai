"""Corroboration assessment for discovered signals.

Discovery surfaces "signals" (evidence) about a startup, each carrying a
source_label, plus a set of startup-level source_citations (URLs). Per the
app's data-quality principle, a signal should not be fully trusted until at
least two *distinct* sources corroborate that same signal_type.

Adopted rule (single, consistent spec):
    A signal_type is "corroborated" ONLY when it is supported by at least two
    DISTINCT sources for that same signal_type. A "source" is a distinct
    source identifier (a distinct source_label on the signal, and/or a
    distinct citation string that refers to the same underlying source). A
    label and a citation that point at the same underlying source count as
    ONE. The GLOBAL number of citations never, by itself, promotes an
    individual signal_type to corroborated: corroboration is evaluated
    per signal_type against its own distinct supporting sources.

This module is a pure, self-contained helper: no I/O, no network, no imports
from other backend modules. It only inspects the dicts/lists it is given and
returns a plain dataclass describing, per signal_type, how many distinct
sources back it and whether that clears the corroboration bar, plus
human-readable notes suitable for attaching to a brief.
"""
from dataclasses import dataclass, field

# A signal_type needs at least this many distinct sources to be corroborated.
_CORROBORATION_THRESHOLD = 2


@dataclass
class SignalTypeAssessment:
    """Per-signal-type corroboration breakdown."""

    signal_type: str
    distinct_source_count: int
    corroborated: bool
    sources: list[str] = field(default_factory=list)


@dataclass
class CorroborationResult:
    corroborated_signal_types: list[str] = field(default_factory=list)
    single_source_signal_types: list[str] = field(default_factory=list)
    # Global count of distinct sources across all labels and citations. This is
    # informational only; it does NOT feed per-signal-type corroboration.
    distinct_source_count: int = 0
    # Per-signal-type breakdown, keyed by signal_type (first-seen order).
    by_signal_type: dict[str, SignalTypeAssessment] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _normalize(value: str | None) -> str | None:
    """Return a case-folded, whitespace-trimmed identifier, or None if empty."""
    if not value:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped.casefold()


def _signal_citation(signal: dict) -> str | None:
    """A signal may optionally carry its own citation identifier under a few
    common keys. Returns the first non-empty one, normalized, else None."""
    for key in ("source_citation", "source_url", "citation", "url"):
        norm = _normalize(signal.get(key))
        if norm:
            return norm
    return None


def assess_corroboration(
    signals: list[dict],
    source_citations: list[str],
) -> CorroborationResult:
    """Assess how well-corroborated each signal_type is.

    signals: dicts with at least 'signal_type' and 'source_label'. A signal
        may optionally carry its own citation (see _signal_citation).
    source_citations: distinct public URLs backing the discovery as a whole.

    Corroboration is per signal_type: a type is corroborated only when its own
    distinct supporting sources number >= 2. Global citations of OTHER types
    never promote a single-source type.
    """
    signals = signals or []
    source_citations = source_citations or []

    distinct_citations = {norm for c in source_citations if (norm := _normalize(c))}
    distinct_labels = {
        norm for s in signals if (norm := _normalize(s.get("source_label")))
    }
    # Global, informational tally only: a label and a citation that name the
    # same underlying source dedupe to one entry via set union.
    distinct_source_count = len(distinct_citations | distinct_labels)

    # Gather the distinct supporting sources for each signal_type. A source is
    # either a source_label on the signal or a citation the signal itself
    # carries; the two dedupe against each other when identical (same source =
    # one). The startup-level source_citations pool is deliberately NOT folded
    # in here, so unrelated citations of other types cannot promote a type.
    sources_by_type: dict[str, set[str]] = {}
    ordered_types: list[str] = []  # preserve first-seen order for stable output
    for signal in signals:
        signal_type = signal.get("signal_type")
        if not signal_type:
            continue
        if signal_type not in sources_by_type:
            sources_by_type[signal_type] = set()
            ordered_types.append(signal_type)
        label = _normalize(signal.get("source_label"))
        if label:
            sources_by_type[signal_type].add(label)
        own_citation = _signal_citation(signal)
        if own_citation:
            sources_by_type[signal_type].add(own_citation)

    corroborated: list[str] = []
    single_source: list[str] = []
    by_signal_type: dict[str, SignalTypeAssessment] = {}
    notes: list[str] = []
    for signal_type in ordered_types:
        sources = sorted(sources_by_type[signal_type])
        count = len(sources)
        is_corroborated = count >= _CORROBORATION_THRESHOLD
        by_signal_type[signal_type] = SignalTypeAssessment(
            signal_type=signal_type,
            distinct_source_count=count,
            corroborated=is_corroborated,
            sources=sources,
        )
        if is_corroborated:
            corroborated.append(signal_type)
            notes.append(f"{signal_type}: corroborated ({count} sources)")
        else:
            single_source.append(signal_type)
            notes.append(
                f"{signal_type}: single-source ({count}) — treat as directional"
            )

    return CorroborationResult(
        corroborated_signal_types=corroborated,
        single_source_signal_types=single_source,
        distinct_source_count=distinct_source_count,
        by_signal_type=by_signal_type,
        notes=notes,
    )
