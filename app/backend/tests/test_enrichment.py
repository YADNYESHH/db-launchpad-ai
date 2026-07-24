"""Tests for free, no-API-key public-registry enrichment (GLEIF LEI).

Every test is OFFLINE: the HTTP layer is either disabled via the env guard or
monkeypatched, so no real network call is ever made. This proves the two core
guarantees: (1) enrichment is offline-safe/disable-able by default, and (2) any
failure degrades gracefully to None without ever raising.
"""
from ..discovery import enrichment
from ..discovery.enrichment import enrich_profile_note, lookup_lei

# A canned GLEIF `/lei-records` payload (shape as returned by the public API).
_CANNED_GLEIF = {
    "data": [
        {
            "type": "lei-records",
            "id": "5493001KJTIIGC8Y1R12",
            "attributes": {
                "lei": "5493001KJTIIGC8Y1R12",
                "entity": {
                    "legalName": {"name": "Bloomberg Finance L.P.", "language": "en"},
                    "legalJurisdiction": "US-DE",
                    "status": "ACTIVE",
                },
                "registration": {"status": "ISSUED"},
            },
        }
    ]
}


def test_lookup_disabled_returns_none_without_network(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", False)

    def _no_network(*args, **kwargs):
        raise AssertionError("network must not be called when enrichment is disabled")

    monkeypatch.setattr(enrichment, "_http_get_json", _no_network)
    assert lookup_lei("Bloomberg Finance L.P.") is None


def test_lookup_returns_none_on_http_failure(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", True)

    def _raise(*args, **kwargs):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(enrichment, "_http_get_json", _raise)
    # Must swallow the error and return None — no exception may propagate.
    assert lookup_lei("AnyCo") is None


def test_lookup_returns_none_on_empty_data(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", True)
    monkeypatch.setattr(enrichment, "_http_get_json", lambda url, timeout: {"data": []})
    assert lookup_lei("Ghost Company") is None


def test_lookup_returns_none_for_blank_name(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", True)

    def _no_network(*args, **kwargs):
        raise AssertionError("network must not be called for a blank name")

    monkeypatch.setattr(enrichment, "_http_get_json", _no_network)
    assert lookup_lei("   ") is None


def test_lookup_happy_path_parses_dict(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", True)
    monkeypatch.setattr(enrichment, "_http_get_json", lambda url, timeout: _CANNED_GLEIF)

    rec = lookup_lei("Bloomberg Finance L.P.")
    assert rec == {
        "lei": "5493001KJTIIGC8Y1R12",
        "legal_name": "Bloomberg Finance L.P.",
        "jurisdiction": "US-DE",
        "status": "ISSUED",
        "source_url": "https://search.gleif.org/#/record/5493001KJTIIGC8Y1R12",
    }


def test_enrich_profile_note_none_when_lookup_none(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", True)
    monkeypatch.setattr(enrichment, "lookup_lei", lambda *args, **kwargs: None)
    assert enrich_profile_note("Whatever Inc") == (None, None)


def test_enrich_profile_note_none_when_disabled(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", False)
    assert enrich_profile_note("Bloomberg Finance L.P.") == (None, None)


def test_enrich_profile_note_happy_path(monkeypatch):
    monkeypatch.setattr(enrichment, "ENRICHMENT_ENABLED", True)
    monkeypatch.setattr(enrichment, "_http_get_json", lambda url, timeout: _CANNED_GLEIF)

    note, citation = enrich_profile_note("Bloomberg Finance L.P.")
    assert note == (
        "Verified legal entity: Bloomberg Finance L.P. "
        "(LEI 5493001KJTIIGC8Y1R12, US-DE, ISSUED)"
    )
    assert citation == "https://search.gleif.org/#/record/5493001KJTIIGC8Y1R12"
