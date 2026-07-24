"""Free, no-API-key public-registry enrichment for live-discovered startups.

The goal is to *strengthen* live discovery with VERIFIABLE public facts, never
to fabricate anything. We query the GLEIF LEI public API (Global Legal Entity
Identifier Foundation), which needs NO API key and returns legal-entity records
(LEI code, legal name, jurisdiction, registration status). If a discovered
company matches a registered legal entity, we can attach that verifiable fact
plus a citation URL.

Design guarantees:
- FREE + KEYLESS: GLEIF's public API requires no authentication.
- HONEST: only facts returned by the registry are used; nothing is invented.
- FULLY GRACEFUL: any failure (no network, timeout, bad JSON, no match) simply
  returns None. These functions NEVER raise.
- OFFLINE-SAFE BY DEFAULT IN TESTS: the ``REGISTRY_ENRICHMENT`` env guard lets
  callers disable it entirely, in which case no network call is ever made.
"""
import json
import logging
import os
import sys
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

# GLEIF LEI public API — no key required.
_GLEIF_BASE = "https://api.gleif.org/api/v1/lei-records"


def _enrichment_enabled_default() -> bool:
    """Env guard so enrichment can be disabled (e.g. offline runs, tests).

    Any of "0"/"false"/"False" disables it; anything else (default "1")
    enables it. When ``REGISTRY_ENRICHMENT`` is not set at all, enrichment is
    auto-disabled under pytest so the test suite and offline runs never hit the
    network by accident.
    """
    raw = os.getenv("REGISTRY_ENRICHMENT")
    if raw is not None:
        return raw not in ("0", "false", "False")
    return not ("PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules)


# Module-level flag; monkeypatch this (or set REGISTRY_ENRICHMENT) to toggle.
ENRICHMENT_ENABLED = _enrichment_enabled_default()


def _build_url(legal_name: str) -> str:
    """Build the GLEIF query URL filtering by exact legal name, top match only."""
    params = urllib.parse.urlencode(
        {"filter[entity.legalName]": legal_name, "page[size]": "1"}
    )
    return f"{_GLEIF_BASE}?{params}"


def _http_get_json(url: str, timeout: float) -> dict | None:
    """Fetch and parse JSON from ``url``.

    Prefers ``httpx`` if importable, else falls back to ``urllib.request``.
    Kept as a single small seam so tests can monkeypatch the whole HTTP layer.
    May raise on network/parse errors — callers must handle that.
    """
    headers = {"Accept": "application/vnd.api+json"}
    try:
        import httpx  # type: ignore
    except ImportError:
        httpx = None  # type: ignore

    if httpx is not None:
        resp = httpx.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        return resp.json()

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (trusted GLEIF host)
        return json.loads(r.read().decode("utf-8"))


def _parse_record(payload: dict) -> dict | None:
    """Parse a GLEIF response into our small verified-fact dict, defensively."""
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    rec = data[0]
    if not isinstance(rec, dict):
        return None

    attrs = rec.get("attributes") or {}
    lei = attrs.get("lei") or rec.get("id")

    entity = attrs.get("entity") or {}
    legal_name_obj = entity.get("legalName")
    legal_name = legal_name_obj.get("name") if isinstance(legal_name_obj, dict) else legal_name_obj

    jurisdiction = entity.get("legalJurisdiction") or entity.get("jurisdiction") or ""

    registration = attrs.get("registration") or {}
    status = registration.get("status") or entity.get("status") or ""

    if not lei or not legal_name:
        return None

    return {
        "lei": str(lei),
        "legal_name": str(legal_name),
        "jurisdiction": str(jurisdiction),
        "status": str(status),
        "source_url": f"https://search.gleif.org/#/record/{lei}",
    }


def lookup_lei(legal_name: str, timeout: float = 4.0) -> dict | None:
    """Look up a legal entity by name via the free GLEIF LEI API.

    Returns a small verified-fact dict for the best match::

        {"lei", "legal_name", "jurisdiction", "status", "source_url"}

    Returns ``None`` on any failure, timeout, no match, or when enrichment is
    disabled. Never raises.
    """
    if not ENRICHMENT_ENABLED:
        return None
    name = (legal_name or "").strip()
    if not name:
        return None
    try:
        payload = _http_get_json(_build_url(name), timeout)
        if not isinstance(payload, dict):
            return None
        return _parse_record(payload)
    except Exception as exc:  # fully defensive — enrichment must never break callers
        logger.debug("GLEIF LEI lookup failed for %r: %s", name, exc)
        return None


def enrich_profile_note(legal_name: str) -> tuple[str | None, str | None]:
    """Return ``(note, citation_url)`` describing a verified legal entity.

    ``note`` is a short human-readable string like
    "Verified legal entity: <name> (LEI <code>, <jurisdiction>, <status>)".
    Returns ``(None, None)`` when enrichment is disabled or no match is found.
    """
    if not ENRICHMENT_ENABLED:
        return None, None
    rec = lookup_lei(legal_name)
    if not rec:
        return None, None
    note = (
        f"Verified legal entity: {rec['legal_name']} "
        f"(LEI {rec['lei']}, {rec['jurisdiction']}, {rec['status']})"
    )
    return note, rec["source_url"]
