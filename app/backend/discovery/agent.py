"""Discovery Agent — the one genuinely-live stage in the system.

Given a sector, it asks Gemini (grounded on live Google Search) to name real,
currently-operating startups and return, for each, the publicly-knowable
fields the scoring pipeline needs, plus the source URLs the grounded search
actually used. Those citations become the evidence trail.

Design guarantees, consistent with the rest of the app:
- LIVE-BUT-HONEST: only publicly-observable fields are populated from
  discovery (profile, expansion signals). Private banking data (payment
  volumes, pain points) is NOT invented here — it is left absent, so the
  existing missing-data governance correctly flags a discovered startup as
  needing client-permissioned data before high-priority outreach. Any
  estimated public figure (e.g. revenue) is marked as an estimate.
- GRACEFUL FALLBACK: any failure (grounding unavailable, model error, bad
  JSON) returns an empty list with a reason string. The caller keeps the
  synthetic NovaTrade seed as a reliable demo anchor. The app never breaks
  because discovery failed.
- EXPLAINABLE: every discovered startup carries the real source URLs the
  grounded search surfaced, stored on the profile and shown in the UI.
"""
import json
import logging
import os
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_PROJECT_ID = os.environ.get("PROJECT_ID", "hack-team-toruk-makto")
_LOCATION = os.environ.get("VERTEX_LOCATION", "europe-west1")
_MODEL_NAME = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash-001")


@dataclass
class DiscoveredStartup:
    name: str
    sector: str
    hq_country: str
    current_countries: list[str]
    target_countries: list[str]
    growth_stage: str
    funding_stage: str
    estimated_annual_revenue_eur: float
    expansion_timeline_months: int | None
    # Each signal is enriched (public-only): {signal_type, country, evidence_note,
    # confidence, signal_date, source_url}. Downstream mapper only reads the first
    # four keys; the date/source_url ride along as extra evidence for the UI trail.
    expansion_signals: list[dict]
    discovery_note: str
    source_citations: list[str] = field(default_factory=list)
    # --- Optional public-enrichment fields (added for coverage, never fabricated) ---
    # All default to a safe empty/None so the mapper contract is unchanged: mapper
    # does not read these, and any omission from the LLM leaves an honest gap.
    funding_amount_eur: float | None = None
    revenue_band: str | None = None
    employee_count_band: str | None = None
    payment_corridors: list[str] = field(default_factory=list)


_DISCOVERY_PROMPT_TEMPLATE = """You are a corporate-banking research analyst. Using live web search, \
identify {n} real, currently-operating startups or scaleups in the "{sector}" sector that show \
genuine cross-border EXPANSION signals (entering new markets, cross-border customers or suppliers, \
international hiring, or fresh funding earmarked for expansion). Prefer European-headquartered \
companies where possible. Only include companies that actually exist and are trading today.

HONESTY RULES (critical):
- Return ONLY values you can support from a real public source found in your search results.
- If a value is NOT supported by a real public source, set it to null. Do NOT guess, infer, or \
fabricate any number, date, country, or corridor. A null is far better than an invented value.
- Do not invent private banking data (payment volumes, internal financials). Where a public \
figure can only be estimated (e.g. revenue), keep it conservative and mark it clearly as a band \
in "revenue_band" rather than a false-precision number.
- For every expansion signal, include the real source URL that supports it whenever one exists.

Return a JSON array (and nothing else) where each element has exactly these keys:
- "name": string
- "sector": string (specific sub-sector)
- "hq_country": string (headquarters country) or null
- "current_countries": array of country name strings it already operates in (empty array if unknown)
- "target_countries": array of country name strings it is expanding into (empty array if unknown)
- "growth_stage": one of "Seed", "Series A", "Series B", "Series C", "Scaleup", "Growth" or null
- "funding_stage": string (e.g. "Series B") or null
- "funding_amount_eur": number in EUR of the most recent disclosed round, or null if not public
- "estimated_annual_revenue_eur": number in EUR (conservative public estimate) or 0 if truly unknown
- "revenue_band": short public revenue band string (e.g. "€10M-€50M ARR") or null if no source
- "employee_count_band": short headcount band string (e.g. "51-200 employees") or null if unknown
- "target_payment_corridors": array of likely cross-border payment corridor strings using ISO-style \
country codes (e.g. "DE-GB", "DE-SG") derived from HQ + target markets, or empty array if unclear
- "expansion_timeline_months": integer months until next market go-live if publicly stated, else null
- "expansion_signals": array of objects, each with:
    - "signal_type": one of "new_country_launch", "international_hiring", "foreign_customer_growth", "supplier_expansion", "funding_event"
    - "country": country name string or null
    - "signal_date": ISO date (YYYY-MM-DD) or year string of the public evidence, or null if undated
    - "evidence_note": one short sentence describing the public evidence
    - "source_url": the real URL of the public source for this signal, or null if none is available
    - "confidence": number between 0 and 1 reflecting how well-supported this signal is
- "discovery_note": one sentence stating what public evidence backs this entry and that any figures \
are estimates

Return strictly valid JSON, no markdown fences, no commentary. Omit (null) anything you cannot ground."""


def _extract_json_array(text: str) -> list[dict]:
    """Pull the first JSON array out of the model's text, tolerating stray
    markdown fences or prose around it."""
    text = text.strip()
    # Strip markdown code fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # Find the outermost [...] array.
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON array found in model output")
    return json.loads(text[start : end + 1])


def _opt_str(value) -> str | None:
    """Coerce a value to a trimmed non-empty string, or None. Never raises."""
    if value is None:
        return None
    try:
        s = str(value).strip()
    except Exception:  # noqa: BLE001 - parsing must never break discovery
        return None
    return s or None


def _opt_float(value) -> float | None:
    """Coerce to a non-negative float, or None when absent/unparseable. Never raises."""
    if value in (None, ""):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f >= 0 else None


def _str_list(value) -> list[str]:
    """Coerce a value into a list of trimmed non-empty strings. Never raises."""
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        s = _opt_str(item)
        if s:
            out.append(s)
    return out


def _clean_signals(raw_signals) -> list[dict]:
    """Normalise expansion signals defensively, preserving the four keys the
    mapper reads (signal_type, country, evidence_note, confidence) and carrying
    the enrichment keys (signal_date, source_url) along for the evidence trail.
    Unparseable entries are skipped rather than raising."""
    out: list[dict] = []
    if not isinstance(raw_signals, list):
        return out
    for s in raw_signals:
        if not isinstance(s, dict):
            continue
        out.append(
            {
                "signal_type": _opt_str(s.get("signal_type")) or "",
                "country": _opt_str(s.get("country")),
                "evidence_note": _opt_str(s.get("evidence_note")) or "",
                "confidence": s.get("confidence", 0.6),
                "signal_date": _opt_str(s.get("signal_date")),
                "source_url": _opt_str(s.get("source_url") or s.get("source")),
            }
        )
    return out



def _grounding_locations() -> list[str]:
    """Locations to try for grounded generation, in order, de-duplicated.

    Gemini 2.0 grounding via ``google_search`` is not offered in every region,
    so we try the configured region first, then fall back to the global and
    us-central1 endpoints before giving up.
    """
    ordered = [_LOCATION, "global", "us-central1"]
    seen: list[str] = []
    for loc in ordered:
        if loc and loc not in seen:
            seen.append(loc)
    return seen


class _GroundedModel:
    """Thin adapter exposing ``generate_content(prompt)`` over the google-genai
    SDK with the Gemini-2.0 ``google_search`` grounding tool.

    IMPORTANT: Gemini 2.0 models require the ``google_search`` tool; the legacy
    ``google_search_retrieval`` tool is only valid for Gemini 1.5 and is
    rejected by 2.0 models (this was the cause of live discovery failing in
    production). We try each candidate region until one succeeds.
    """

    def generate_content(self, prompt: str):
        from google import genai
        from google.genai import types

        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        )
        last_exc: Exception | None = None
        for loc in _grounding_locations():
            try:
                client = genai.Client(vertexai=True, project=_PROJECT_ID, location=loc)
                return client.models.generate_content(
                    model=_MODEL_NAME, contents=prompt, config=config
                )
            except Exception as exc:  # noqa: BLE001 - try the next region
                last_exc = exc
                logger.warning("Grounded generation failed in region %s.", loc, exc_info=True)
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("No grounding region available.")


def _get_grounded_model():
    return _GroundedModel()


def _collect_citations(response) -> list[str]:
    """Best-effort extraction of the real source URLs the grounded search used.
    Grounding metadata shape varies across SDK versions, so this is defensive."""
    urls: list[str] = []
    try:
        for candidate in getattr(response, "candidates", []) or []:
            meta = getattr(candidate, "grounding_metadata", None)
            if not meta:
                continue
            for chunk in getattr(meta, "grounding_chunks", []) or []:
                web = getattr(chunk, "web", None)
                uri = getattr(web, "uri", None) if web else None
                if uri and uri not in urls:
                    urls.append(uri)
    except Exception:  # noqa: BLE001 - citation extraction must never break discovery
        logger.warning("Could not extract grounding citations.", exc_info=True)
    return urls


def discover_startups(sector: str, limit: int = 4) -> tuple[list[DiscoveredStartup], str | None]:
    """Returns (discovered_startups, error_reason). On any failure the list is
    empty and error_reason explains why, so the caller degrades gracefully."""
    sector = sector.strip()
    if not sector:
        return [], "Sector query was empty."

    try:
        model = _get_grounded_model()
    except Exception:  # noqa: BLE001
        logger.warning("Discovery unavailable: could not initialise grounded Gemini model.", exc_info=True)
        return [], "Live discovery is unavailable in this environment (Vertex AI grounding could not initialise)."

    prompt = _DISCOVERY_PROMPT_TEMPLATE.format(n=limit, sector=sector)
    try:
        response = model.generate_content(prompt)
        raw = (response.text or "").strip()
    except Exception:  # noqa: BLE001
        logger.warning("Discovery failed during model call.", exc_info=True)
        return [], "Live discovery call failed; the synthetic example remains available."

    citations = _collect_citations(response)

    try:
        records = _extract_json_array(raw)
    except (ValueError, json.JSONDecodeError):
        logger.warning("Discovery returned unparseable output.", exc_info=True)
        return [], "Live discovery returned an unparseable response; the synthetic example remains available."

    discovered: list[DiscoveredStartup] = []
    for rec in records:
        if not isinstance(rec, dict) or not rec.get("name"):
            continue
        try:
            discovered.append(
                DiscoveredStartup(
                    name=str(rec["name"]).strip(),
                    sector=str(rec.get("sector", sector)).strip() or sector,
                    hq_country=str(rec.get("hq_country") or "Unknown").strip() or "Unknown",
                    current_countries=_str_list(rec.get("current_countries")),
                    target_countries=_str_list(rec.get("target_countries")),
                    growth_stage=str(rec.get("growth_stage") or "Scaleup").strip() or "Scaleup",
                    funding_stage=str(rec.get("funding_stage") or "Unknown").strip() or "Unknown",
                    estimated_annual_revenue_eur=max(0.0, float(rec.get("estimated_annual_revenue_eur", 0) or 0)),
                    expansion_timeline_months=(
                        int(rec["expansion_timeline_months"])
                        if rec.get("expansion_timeline_months") not in (None, "")
                        else None
                    ),
                    expansion_signals=_clean_signals(rec.get("expansion_signals")),
                    discovery_note=str(rec.get("discovery_note", "")).strip(),
                    source_citations=list(citations),
                    funding_amount_eur=_opt_float(rec.get("funding_amount_eur")),
                    revenue_band=_opt_str(rec.get("revenue_band")),
                    employee_count_band=_opt_str(rec.get("employee_count_band")),
                    payment_corridors=_str_list(
                        rec.get("target_payment_corridors") or rec.get("payment_corridors")
                    ),
                )
            )
        except (TypeError, ValueError):
            logger.warning("Skipping a malformed discovered record.", exc_info=True)
            continue

    if not discovered:
        return [], "Live discovery did not return any usable startups for that sector."

    return discovered, None
