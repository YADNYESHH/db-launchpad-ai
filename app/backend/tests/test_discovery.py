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
    # The discovered citation must be preserved. Mapper may additively append
    # optional public-registry (GLEIF) citations, so assert membership, not equality.
    assert "https://example.com/realco-series-b" in profile.source_citations
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


# ---------------------------------------------------------------------------
# Parsing-path tests (yadnyesh): feed canned raw LLM text through discover_startups
# by monkeypatching the grounded-model call. No real network / LLM calls happen.
# ---------------------------------------------------------------------------

from types import SimpleNamespace  # noqa: E402

from ..discovery import agent as _agent  # noqa: E402


def _fake_response(text: str, uris: list[str] | None = None):
    """Build a minimal object shaped like the Vertex response the agent reads:
    it exposes `.text` and `.candidates[].grounding_metadata.grounding_chunks[].web.uri`."""
    chunks = [SimpleNamespace(web=SimpleNamespace(uri=u)) for u in (uris or [])]
    candidate = SimpleNamespace(grounding_metadata=SimpleNamespace(grounding_chunks=chunks))
    return SimpleNamespace(text=text, candidates=[candidate])


def _patch_model(monkeypatch, response):
    """Make the agent's model factory return a stub whose generate_content()
    yields our canned response, so the deterministic parsing path is exercised."""
    stub = SimpleNamespace(generate_content=lambda _prompt: response)
    monkeypatch.setattr(_agent, "_get_grounded_model", lambda: stub)


_CANNED_JSON = """Here are the companies I found:
```json
[
  {
    "name": "PayCross GmbH",
    "sector": "Cross-border payments",
    "hq_country": "Germany",
    "current_countries": ["Germany", "France"],
    "target_countries": ["United Kingdom", "Singapore"],
    "growth_stage": "Series B",
    "funding_stage": "Series B",
    "funding_amount_eur": 25000000,
    "estimated_annual_revenue_eur": 18000000,
    "revenue_band": "\u20ac10M-\u20ac50M ARR",
    "employee_count_band": "51-200 employees",
    "target_payment_corridors": ["DE-GB", "DE-SG"],
    "expansion_timeline_months": 6,
    "expansion_signals": [
      {
        "signal_type": "new_country_launch",
        "country": "Singapore",
        "signal_date": "2026-03-01",
        "evidence_note": "Opened an APAC office in Singapore.",
        "source_url": "https://example.com/paycross-apac",
        "confidence": 0.85
      },
      {
        "signal_type": "funding_event",
        "country": null,
        "signal_date": null,
        "evidence_note": "Raised a Series B round.",
        "source_url": null,
        "confidence": 0.9
      }
    ],
    "discovery_note": "Based on public press coverage; figures are estimates."
  },
  {
    "name": "NullFields Ltd",
    "sector": "Cross-border payments",
    "hq_country": null,
    "current_countries": [],
    "target_countries": [],
    "growth_stage": null,
    "funding_stage": null,
    "funding_amount_eur": null,
    "estimated_annual_revenue_eur": 0,
    "revenue_band": null,
    "employee_count_band": null,
    "target_payment_corridors": [],
    "expansion_timeline_months": null,
    "expansion_signals": [],
    "discovery_note": "Sparse public footprint; most fields not grounded."
  }
]
```
Hope this helps!"""


def test_discover_startups_parses_canned_llm_output_with_null_fields(monkeypatch):
    _patch_model(monkeypatch, _fake_response(_CANNED_JSON, uris=["https://example.com/paycross-apac"]))

    result, reason = discover_startups("cross-border payments", limit=2)

    assert reason is None
    assert len(result) == 2

    rich, sparse = result[0], result[1]

    # Fully-populated record keeps its grounded public fields.
    assert rich.name == "PayCross GmbH"
    assert rich.hq_country == "Germany"
    assert rich.funding_amount_eur == 25_000_000
    assert rich.revenue_band == "\u20ac10M-\u20ac50M ARR"
    assert rich.employee_count_band == "51-200 employees"
    assert rich.payment_corridors == ["DE-GB", "DE-SG"]
    assert rich.expansion_timeline_months == 6

    # Enrichment keys ride along on each signal for the evidence trail.
    launch = rich.expansion_signals[0]
    assert launch["signal_type"] == "new_country_launch"
    assert launch["signal_date"] == "2026-03-01"
    assert launch["source_url"] == "https://example.com/paycross-apac"

    # Grounding citations were extracted from the response metadata.
    assert rich.source_citations == ["https://example.com/paycross-apac"]

    # Null / omitted fields degrade to safe defaults without crashing.
    assert sparse.name == "NullFields Ltd"
    assert sparse.hq_country == "Unknown"
    assert sparse.growth_stage == "Scaleup"
    assert sparse.funding_stage == "Unknown"
    assert sparse.funding_amount_eur is None
    assert sparse.revenue_band is None
    assert sparse.employee_count_band is None
    assert sparse.payment_corridors == []
    assert sparse.current_countries == []
    assert sparse.expansion_timeline_months is None
    assert sparse.estimated_annual_revenue_eur == 0.0

    # The parsed records still satisfy the mapper contract (no exceptions).
    profile, _payment, signals = to_models(rich)
    assert profile.name == "PayCross GmbH"
    assert all(s.source_type == DataSourceType.LIVE_GROUNDED for s in signals)


def test_discover_startups_malformed_payload_returns_reason(monkeypatch):
    _patch_model(monkeypatch, _fake_response("Sorry, I could not find anything useful today."))

    result, reason = discover_startups("cross-border payments", limit=2)

    assert result == []
    assert reason is not None


def test_discover_startups_broken_json_returns_reason_without_raising(monkeypatch):
    # A JSON array that starts correctly but is truncated / invalid must not raise.
    _patch_model(monkeypatch, _fake_response('[{"name": "Broken", "sector": '))

    result, reason = discover_startups("cross-border payments", limit=2)

    assert result == []
    assert reason is not None


def test_discover_startups_omitted_optional_keys_use_defaults(monkeypatch):
    # A minimal but valid record omitting every optional key must parse cleanly.
    _patch_model(monkeypatch, _fake_response('[{"name": "MinimalCo"}]'))

    result, reason = discover_startups("cross-border payments", limit=1)

    assert reason is None
    assert len(result) == 1
    only = result[0]
    assert only.name == "MinimalCo"
    assert only.hq_country == "Unknown"
    assert only.current_countries == []
    assert only.expansion_signals == []
    assert only.funding_amount_eur is None
    assert only.payment_corridors == []


# ---------------------------------------------------------------------------
# diagnose_discovery tests (yadnyesh): the admin-facing diagnostic must SURFACE
# the real error on failure and report citations/text on success, all without
# any real network / LLM calls. We stub the same `_get_grounded_model` seam the
# other tests use so no google-genai client is ever constructed.
# ---------------------------------------------------------------------------

from ..discovery.agent import diagnose_discovery  # noqa: E402


def test_diagnose_discovery_reports_error_without_raising(monkeypatch):
    def _boom():
        raise RuntimeError("google_search tool not supported: token=SECRET_SHOULD_NOT_LEAK")

    monkeypatch.setattr(_agent, "_get_grounded_model", _boom)

    diag = diagnose_discovery("cross-border payments")

    assert diag["ok"] is False
    assert diag["error_type"] == "RuntimeError"
    assert diag["error_message"] is not None
    assert "google_search tool not supported" in diag["error_message"]
    assert len(diag["error_message"]) <= 500
    assert diag["has_text"] is False
    assert diag["num_citations"] == 0
    assert diag["raw_preview"] is None
    assert diag["model"] == _agent._MODEL_NAME


def test_diagnose_discovery_reports_error_when_generation_raises(monkeypatch):
    # Factory succeeds but the grounded call itself raises: still surfaced, never raised.
    stub = SimpleNamespace(
        generate_content=lambda _p: (_ for _ in ()).throw(ValueError("region exhausted")),
        last_region="us-central1",
    )
    monkeypatch.setattr(_agent, "_get_grounded_model", lambda: stub)

    diag = diagnose_discovery("cross-border payments")

    assert diag["ok"] is False
    assert diag["error_type"] == "ValueError"
    assert "region exhausted" in diag["error_message"]
    assert diag["region"] == "us-central1"


def test_diagnose_discovery_reports_success_with_citations(monkeypatch):
    canned = _fake_response(
        '[{"name": "PayCross GmbH"}]',
        uris=["https://example.com/a", "https://example.com/b"],
    )
    _patch_model(monkeypatch, canned)

    diag = diagnose_discovery("cross-border payments")

    assert diag["ok"] is True
    assert diag["error_type"] is None
    assert diag["error_message"] is None
    assert diag["has_text"] is True
    assert diag["num_citations"] == 2
    assert diag["raw_preview"].startswith('[{"name": "PayCross GmbH"}]')



