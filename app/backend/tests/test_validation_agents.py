"""Tests for the self-validation capabilities added to the existing
ingestion and recommendation stages (see orchestrator/validation.py) -
duplicate detection, source credibility, freshness, and output validation.
No new agents are introduced; these are checks the existing stages perform
on their own inputs/outputs before handing off to the next stage.
"""
from datetime import date, timedelta

from ..models.enums import ApprovalStatus, ConfidenceBand, DataSourceType, PriorityBand
from ..models.profile import ExpansionSignal, StartupProfile
from ..models.recommendation import RecommendationRecord
from ..orchestrator.recommend import generate_recommendation
from ..orchestrator.validation import (
    check_data_freshness,
    check_source_credibility,
    find_duplicate_profile,
    find_duplicate_signals,
    validate_recommendation_output,
)


def _profile(startup_id: str, name: str, hq_country: str) -> StartupProfile:
    return StartupProfile(
        startup_id=startup_id,
        name=name,
        sector="Test",
        hq_country=hq_country,
        growth_stage="Seed",
        funding_stage="Seed",
        annual_revenue_eur=1000,
    )


def _signal(signal_id: str, days_old: int, confidence: float, note: str = "note") -> ExpansionSignal:
    return ExpansionSignal(
        signal_id=signal_id,
        startup_id="ST-X",
        signal_type="foreign_customer_growth",
        country="Ireland",
        signal_date=date.today() - timedelta(days=days_old),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="test",
        confidence=confidence,
        evidence_note=note,
    )


def test_find_duplicate_profile_matches_on_name_and_country_case_insensitive():
    existing = [_profile("ST-001", "NovaTrade AI GmbH", "Germany")]
    candidate = _profile("ST-999", "novatrade ai gmbh", "germany")
    dup = find_duplicate_profile(existing, candidate)
    assert dup is not None
    assert dup.startup_id == "ST-001"


def test_find_duplicate_profile_ignores_self():
    existing = [_profile("ST-001", "NovaTrade AI GmbH", "Germany")]
    candidate = _profile("ST-001", "NovaTrade AI GmbH", "Germany")
    assert find_duplicate_profile(existing, candidate) is None


def test_find_duplicate_profile_no_match_for_different_company():
    existing = [_profile("ST-001", "NovaTrade AI GmbH", "Germany")]
    candidate = _profile("ST-002", "Other Co", "France")
    assert find_duplicate_profile(existing, candidate) is None


def test_find_duplicate_signals_detects_repeated_evidence():
    signals = [
        _signal("SIG-1", days_old=10, confidence=0.9, note="Same evidence"),
        _signal("SIG-2", days_old=10, confidence=0.9, note="Same evidence"),
    ]
    duplicates = find_duplicate_signals(signals)
    assert len(duplicates) == 1


def test_find_duplicate_signals_no_false_positive_on_distinct_evidence():
    signals = [
        _signal("SIG-1", days_old=10, confidence=0.9, note="First"),
        _signal("SIG-2", days_old=20, confidence=0.9, note="Second"),
    ]
    assert find_duplicate_signals(signals) == []


def test_check_source_credibility_flags_low_confidence():
    signals = [_signal("SIG-1", days_old=1, confidence=0.3)]
    assert check_source_credibility(signals) is not None


def test_check_source_credibility_passes_high_confidence():
    signals = [_signal("SIG-1", days_old=1, confidence=0.95)]
    assert check_source_credibility(signals) is None


def test_check_data_freshness_flags_stale_evidence():
    signals = [_signal("SIG-1", days_old=400, confidence=0.9)]
    assert check_data_freshness(signals, as_of=date.today()) is not None


def test_check_data_freshness_passes_recent_evidence():
    signals = [_signal("SIG-1", days_old=5, confidence=0.9)]
    assert check_data_freshness(signals, as_of=date.today()) is None


def _valid_recommendation() -> RecommendationRecord:
    return RecommendationRecord(
        recommendation_id="rec-1",
        startup_id="ST-1",
        score_record_id="score-1",
        final_score=85.0,
        priority_band=PriorityBand.HIGH_PRIORITY,
        client_summary="Summary",
        why_now="Because",
        top_drivers=["revenue_potential"],
        suggested_questions=["Q1?"],
        product_themes=["Multi-currency accounts"],
    )


def test_validate_recommendation_output_accepts_well_formed_record():
    assert validate_recommendation_output(_valid_recommendation()) == []


def test_validate_recommendation_output_flags_missing_field():
    rec = _valid_recommendation()
    rec.client_summary = ""
    problems = validate_recommendation_output(rec)
    assert any("client_summary" in p for p in problems)


def test_validate_recommendation_output_flags_out_of_range_score():
    rec = _valid_recommendation()
    rec.final_score = 150.0
    problems = validate_recommendation_output(rec)
    assert any("final_score" in p for p in problems)


def test_novatrade_recommendation_carries_evidence_confidence_and_no_false_duplicate_flags(novatrade_ctx):
    from ..scoring import score_startup

    score_record = score_startup(novatrade_ctx)
    rec, reason = generate_recommendation(
        profile=novatrade_ctx.profile,
        score_record=score_record,
        score_record_id="score-x",
        payment=novatrade_ctx.payment,
        pain=novatrade_ctx.pain,
        signals=novatrade_ctx.signals,
    )
    assert reason is None
    assert rec is not None
    assert rec.evidence_confidence in (ConfidenceBand.HIGH, ConfidenceBand.MEDIUM, ConfidenceBand.LOW)
    assert rec.approval_status == ApprovalStatus.DRAFT
    assert rec.validation_notes == []
    # The seed data's signals are all distinct - no duplicate-evidence caveat expected.
    assert not any("Duplicate signal" in c for c in rec.caveats)
