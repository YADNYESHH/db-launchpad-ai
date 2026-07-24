"""Tests for the Discovery Agent's deterministic parts - JSON extraction,
model mapping, and the graceful-fallback contract. The live grounded Gemini
call itself is not unit-tested (it needs live network + Vertex auth); it is
verified against the deployed service instead. These tests cover everything
around it so a bad model response degrades safely rather than crashing.
"""
from ..discovery.agent import DiscoveredStartup, _extract_json_array, discover_startups
from ..discovery.mapper import to_models
from ..models.enums import DataSourceType


def test_extract_json_array_from_plain_json():
    text = '[{"name": "Acme"}]'
    assert _extract_json_array(text) == [{"name": "Acme"}]


def test_extract_json_array_from_markdown_fenced():
    text = '```json\n[{"name": "Acme"}]\n```'
    assert _extract_json_array(text) == [{"name": "Acme"}]


def test_extract_json_array_with_surrounding_prose():
    text = 'Here are the startups:\n[{"name": "Acme"}]\nHope that helps.'
    assert _extract_json_array(text) == [{"name": "Acme"}]


def test_extract_json_array_raises_when_no_array():
    import pytest

    with pytest.raises(ValueError):
        _extract_json_array("no json here")


def test_discover_startups_empty_sector_returns_reason():
    result, reason = discover_startups("   ")
    assert result == []
    assert reason is not None


def _sample_discovered() -> DiscoveredStartup:
    return DiscoveredStartup(
        name="RealCo Ltd",
        sector="ClimateTech",
        hq_country="Germany",
        current_countries=["Germany", "France"],
        target_countries=["United Kingdom", "Singapore"],
        growth_stage="Series B",
        funding_stage="Series B",
        estimated_annual_revenue_eur=12_000_000,
        expansion_timeline_months=6,
        expansion_signals=[
            {"signal_type": "new_country_launch", "country": "Singapore", "evidence_note": "Opened APAC office", "confidence": 0.8},
            {"signal_type": "funding_event", "country": None, "evidence_note": "Raised Series B", "confidence": 0.9},
        ],
        discovery_note="Based on public press coverage.",
        source_citations=["https://example.com/realco-series-b"],
    )


def test_to_models_maps_live_discovered_startup_correctly():
    profile, payment, signals = to_models(_sample_discovered())

    assert profile.synthetic_flag is False
    assert profile.data_source_type == DataSourceType.LIVE_GROUNDED
    assert profile.source_citations == ["https://example.com/realco-series-b"]
    assert "estimate" in profile.discovery_note.lower()
    assert profile.startup_id.startswith("LIVE-")

    # Two valid signals mapped, both flagged as live-grounded.
    assert len(signals) == 2
    assert all(s.source_type == DataSourceType.LIVE_GROUNDED for s in signals)

    # Payment profile is estimated from public revenue signal, not fabricated pain data.
    assert payment is not None
    assert payment.annual_cross_border_payment_value_eur > 0
    assert "EUR" in payment.currencies


def test_to_models_backfills_country_for_country_required_signal():
    d = _sample_discovered()
    # A country-required signal with no country should backfill from target markets, not crash.
    d.expansion_signals = [
        {"signal_type": "new_country_launch", "country": None, "evidence_note": "launch", "confidence": 0.7}
    ]
    profile, payment, signals = to_models(d)
    assert len(signals) == 1
    assert signals[0].country is not None


def test_to_models_skips_invalid_signal_types():
    d = _sample_discovered()
    d.expansion_signals = [
        {"signal_type": "not_a_real_type", "country": "France", "evidence_note": "x", "confidence": 0.5},
        {"signal_type": "foreign_customer_growth", "country": "France", "evidence_note": "y", "confidence": 0.5},
    ]
    _, _, signals = to_models(d)
    assert len(signals) == 1
    assert signals[0].signal_type == "foreign_customer_growth"


def test_to_models_no_payment_when_revenue_unknown():
    d = _sample_discovered()
    d.estimated_annual_revenue_eur = 0
    _, payment, _ = to_models(d)
    assert payment is None
