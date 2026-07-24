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
    expansion_signals: list[dict]  # each: {signal_type, country, evidence_note, confidence}
    discovery_note: str
    source_citations: list[str] = field(default_factory=list)


_DISCOVERY_PROMPT_TEMPLATE = """You are a corporate-banking research analyst. Using live web search, \
identify {n} real, currently-operating startups or scaleups in the "{sector}" sector that are \
plausibly expanding internationally (new markets, cross-border customers or suppliers, or recent \
funding to fund expansion). Prefer European-headquartered companies where possible.

For EACH company, return ONLY facts you can support from search results. Do not invent private \
financial data. If a figure is an estimate, keep it conservative and clearly an estimate.

Return a JSON array (and nothing else) where each element has exactly these keys:
- "name": string
- "sector": string (specific sub-sector)
- "hq_country": string
- "current_countries": array of country name strings (markets it already operates in)
- "target_countries": array of country name strings (markets it is expanding into; may be empty)
- "growth_stage": one of "Seed", "Series A", "Series B", "Series C", "Scaleup", "Growth"
- "funding_stage": string (e.g. "Series B")
- "estimated_annual_revenue_eur": number (a conservative public estimate in EUR; 0 if truly unknown)
- "expansion_timeline_months": integer or null (months until next market go-live if known)
- "expansion_signals": array of objects, each with:
    - "signal_type": one of "new_country_launch", "international_hiring", "foreign_customer_growth", "supplier_expansion", "funding_event"
    - "country": country name string or null
    - "evidence_note": one short sentence describing the public evidence
    - "confidence": number between 0 and 1 reflecting how well-supported this signal is
- "discovery_note": one sentence stating what public evidence backs this entry and that figures are estimates

Return strictly valid JSON, no markdown fences, no commentary."""


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


def _get_grounded_model():
    import vertexai
    from vertexai.generative_models import GenerativeModel, Tool
    from vertexai.generative_models import grounding as grounding_mod

    vertexai.init(project=_PROJECT_ID, location=_LOCATION)
    search_tool = Tool.from_google_search_retrieval(grounding_mod.GoogleSearchRetrieval())
    return GenerativeModel(_MODEL_NAME, tools=[search_tool])


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
                    hq_country=str(rec.get("hq_country", "Unknown")).strip() or "Unknown",
                    current_countries=[str(c).strip() for c in rec.get("current_countries", []) if str(c).strip()],
                    target_countries=[str(c).strip() for c in rec.get("target_countries", []) if str(c).strip()],
                    growth_stage=str(rec.get("growth_stage", "Scaleup")).strip() or "Scaleup",
                    funding_stage=str(rec.get("funding_stage", "Unknown")).strip() or "Unknown",
                    estimated_annual_revenue_eur=max(0.0, float(rec.get("estimated_annual_revenue_eur", 0) or 0)),
                    expansion_timeline_months=(
                        int(rec["expansion_timeline_months"])
                        if rec.get("expansion_timeline_months") not in (None, "")
                        else None
                    ),
                    expansion_signals=[s for s in rec.get("expansion_signals", []) if isinstance(s, dict)],
                    discovery_note=str(rec.get("discovery_note", "")).strip(),
                    source_citations=list(citations),
                )
            )
        except (TypeError, ValueError):
            logger.warning("Skipping a malformed discovered record.", exc_info=True)
            continue

    if not discovered:
        return [], "Live discovery did not return any usable startups for that sector."

    return discovered, None
