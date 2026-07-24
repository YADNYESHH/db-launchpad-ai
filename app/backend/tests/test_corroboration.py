"""Tests for the pure corroboration-assessment helper.

Adopted rule under test: a signal_type is corroborated ONLY when it is
supported by at least two DISTINCT sources for that same signal_type. The
global number of citations never, by itself, promotes an individual
signal_type — corroboration is evaluated per signal_type against its own
distinct supporting sources.
"""
from ..discovery.corroboration import (
    CorroborationResult,
    SignalTypeAssessment,
    assess_corroboration,
)


def test_same_signal_type_two_distinct_sources_is_corroborated():
    signals = [
        {
            "signal_type": "expansion",
            "country": "DE",
            "evidence_note": "Opened a Berlin office",
            "source_label": "TechCrunch",
        },
        {
            "signal_type": "expansion",
            "country": "DE",
            "evidence_note": "Job postings in Berlin",
            "source_label": "LinkedIn",
        },
    ]
    result = assess_corroboration(signals, source_citations=[])

    assert result.corroborated_signal_types == ["expansion"]
    assert result.single_source_signal_types == []
    assert result.by_signal_type["expansion"].distinct_source_count == 2
    assert result.by_signal_type["expansion"].corroborated is True
    assert "expansion: corroborated (2 sources)" in result.notes


def test_single_source_with_matching_citation_stays_single_source():
    # One signal with one source_label, plus a single startup-level citation
    # that names the SAME underlying source. Label + citation refer to one
    # source, so the signal_type stays single-source (NOT corroborated).
    signals = [
        {
            "signal_type": "funding",
            "country": None,
            "evidence_note": "Raised a seed round",
            "source_label": "https://example.com/press",
        }
    ]
    result = assess_corroboration(
        signals, source_citations=["https://example.com/press"]
    )

    assert result.single_source_signal_types == ["funding"]
    assert result.corroborated_signal_types == []
    assert result.by_signal_type["funding"].distinct_source_count == 1
    assert result.by_signal_type["funding"].corroborated is False
    # The label and the citation are the same source, so the global tally is 1.
    assert result.distinct_source_count == 1
    assert "funding: single-source (1) — treat as directional" in result.notes


def test_global_citations_of_other_types_do_not_promote_single_source_type():
    # 'hiring' rests on exactly ONE source. The startup has many citations, but
    # they belong to other evidence, so they must NOT promote 'hiring'.
    signals = [
        {
            "signal_type": "hiring",
            "country": "FR",
            "evidence_note": "Multiple open roles",
            "source_label": "CompanyBlog",
        }
    ]
    citations = [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]
    result = assess_corroboration(signals, source_citations=citations)

    assert result.single_source_signal_types == ["hiring"]
    assert result.corroborated_signal_types == []
    assert result.by_signal_type["hiring"].distinct_source_count == 1
    # Global tally still counts every distinct source (1 label + 3 citations).
    assert result.distinct_source_count == 4
    assert "hiring: single-source (1) — treat as directional" in result.notes


def test_distinct_sources_dedupe_case_insensitively_per_signal_type():
    signals = [
        {
            "signal_type": "funding",
            "country": None,
            "evidence_note": "note one",
            "source_label": "TechCrunch",
        },
        {
            "signal_type": "funding",
            "country": None,
            "evidence_note": "note two",
            "source_label": "techcrunch",  # same source, different case -> one
        },
    ]
    result = assess_corroboration(signals, source_citations=[])

    # 'funding' has only one distinct source once case is folded, so it is NOT
    # corroborated despite two signals.
    assert result.by_signal_type["funding"].distinct_source_count == 1
    assert "funding" in result.single_source_signal_types
    assert "funding" not in result.corroborated_signal_types


def test_mixed_corroborated_and_single_source_notes():
    signals = [
        {"signal_type": "international_hiring", "source_label": "LinkedIn"},
        {"signal_type": "international_hiring", "source_label": "CompanyBlog"},
        {"signal_type": "new_country_launch", "source_label": "PressRelease"},
    ]
    result = assess_corroboration(signals, source_citations=[])

    assert result.corroborated_signal_types == ["international_hiring"]
    assert result.single_source_signal_types == ["new_country_launch"]
    assert result.notes == [
        "international_hiring: corroborated (2 sources)",
        "new_country_launch: single-source (1) — treat as directional",
    ]
    assert isinstance(
        result.by_signal_type["new_country_launch"], SignalTypeAssessment
    )


def test_empty_inputs_do_not_crash():
    result = assess_corroboration([], [])

    assert isinstance(result, CorroborationResult)
    assert result.corroborated_signal_types == []
    assert result.single_source_signal_types == []
    assert result.distinct_source_count == 0
    assert result.by_signal_type == {}
    assert result.notes == []


def test_empty_signals_with_none_source_citations_do_not_crash():
    result = assess_corroboration([], None)  # type: ignore[arg-type]

    assert result.distinct_source_count == 0
    assert result.corroborated_signal_types == []
    assert result.single_source_signal_types == []
    assert result.notes == []


def test_signal_missing_signal_type_is_skipped_gracefully():
    signals = [
        {"country": "US", "evidence_note": "no type here", "source_label": "X"},
        {
            "signal_type": "expansion",
            "country": "US",
            "evidence_note": "valid",
            "source_label": "Y",
        },
    ]
    result = assess_corroboration(signals, source_citations=[])

    assert "expansion" in result.single_source_signal_types
    assert len(result.corroborated_signal_types) + len(result.single_source_signal_types) == 1
