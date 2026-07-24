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
_MODEL_NAME = os.environ.get("VERTEX_MODEL", "gemini-2.5-flash")


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



_WORKING_COMBO: tuple[str, str] | None = None


def _candidate_models() -> list[str]:
    """Model IDs to try, in order, de-duplicated. The hackathon platform serves
    ``gemini-2.5-flash`` (see GCP_SERVICE_ACCOUNTS.md, confirmed live). Both
    ``gemini-2.0-flash`` and ``gemini-flash-latest`` are deliberately NOT in
    this list: both were confirmed live (via /discovery/diagnostics) to 404 as
    "Publisher model ... was not found" on this project, so every attempt
    against them was pure wasted latency (a real contributor to live discovery
    appearing to hang - see ATTEMPT_TIMEOUT_SECONDS below for the other half
    of that fix)."""
    ordered = [_MODEL_NAME, "gemini-2.5-flash", "gemini-2.5-pro"]
    seen: list[str] = []
    for m in ordered:
        if m and m not in seen:
            seen.append(m)
    return seen


def _grounding_locations() -> list[str]:
    """Locations to try for grounded generation, in order, de-duplicated.

    ``global`` is the only location this project's README/GCP_SERVICE_ACCOUNTS.md
    documents as the guaranteed-working example, and is the sole entry now.
    Previously also tried the configured region (``europe-west1``) as a second
    candidate, but every combination that reached that region 404'd the same
    way as the retired models above - it was pure wasted latency on the
    request path, not a real fallback. Trimming to one location roughly halves
    worst-case latency for a single grounded call (see ATTEMPT_TIMEOUT_SECONDS).
    """
    ordered = ["global"]
    seen: list[str] = []
    for loc in ordered:
        if loc and loc not in seen:
            seen.append(loc)
    return seen


# Hard per-attempt cap: a single (model, region) combination gets this long to
# either succeed or fail before we move on. Without this, a hanging or slow
# combination could block the entire request indefinitely - this was confirmed
# live (a diagnostics call did not return within 60 seconds). That first fix
# used 12s, sized to skip dead (404ing) combos quickly. Once those dead combos
# were removed from the candidate matrix (see _candidate_models/_grounding_
# locations above), 12s turned out to be too tight for the *opposite* case: a
# real grounded search+synthesis call that is genuinely working, confirmed
# live via a 504 DEADLINE_EXCEEDED from Google's own server (not our client
# timeout) on the second attempt - i.e. the call needed more than 12s to
# finish, not less. Raised to 25s so a real call has room to complete; worst
# case with the trimmed matrix is now bounded at roughly
# len(models) * len(locations) * ATTEMPT_TIMEOUT_SECONDS = 2 * 1 * 25 = 50s.
ATTEMPT_TIMEOUT_SECONDS = 25


class _GroundedModel:
    """Thin adapter exposing ``generate_content(prompt)`` over the google-genai
    SDK with the Gemini-2.0 ``google_search`` grounding tool.

    IMPORTANT: Gemini 2.0 models require the ``google_search`` tool; the legacy
    ``google_search_retrieval`` tool is only valid for Gemini 1.5 and is
    rejected by 2.0 models (this was the cause of live discovery failing in
    production). We try each candidate region until one succeeds.
    """

    def __init__(self) -> None:
        # Populated by generate_content so callers (e.g. diagnostics) can report
        # which model/region actually served the request, or what was tried last.
        self.success_region: str | None = None
        self.success_model: str | None = None
        self.last_region: str | None = None
        self.last_model: str | None = None
        # Full per-attempt trace (model, region, outcome, elapsed seconds, and a
        # truncated error) for every combo tried in the most recent call. Lets
        # /discovery/diagnostics show exactly what happened to EVERY attempt,
        # not just the last one - the last-only view previously made it look
        # like every combo 404'd when in fact only the retired ones did and the
        # real (working) combo was separately timing out for a different reason.
        self.attempts: list[dict] = []

    def generate_content(self, prompt: str):
        import concurrent.futures
        import time

        from google import genai
        from google.genai import types

        global _WORKING_COMBO
        # First line of defense: ask the SDK's own transport for a bounded
        # timeout (milliseconds) so a slow socket doesn't hang forever.
        http_options = types.HttpOptions(timeout=ATTEMPT_TIMEOUT_SECONDS * 1000)
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        )

        # Try the last-known-good (model, region) first, then the full matrix so
        # a wrong/retired model ID or region self-heals to an available one.
        combos: list[tuple[str, str]] = []
        if _WORKING_COMBO is not None:
            combos.append(_WORKING_COMBO)
        for region in _grounding_locations():
            for model in _candidate_models():
                combos.append((model, region))

        def _call_once(model: str, region: str):
            client = genai.Client(
                vertexai=True, project=_PROJECT_ID, location=region, http_options=http_options
            )
            return client.models.generate_content(model=model, contents=prompt, config=config)

        last_exc: Exception | None = None
        tried: set[tuple[str, str]] = set()
        # Second line of defense: a hard wall-clock cap per attempt, independent
        # of whether the SDK/transport actually honours http_options above. This
        # is what turns "one bad region can hang the whole request" into
        # "one bad region costs at most ATTEMPT_TIMEOUT_SECONDS, then we move on" -
        # confirmed live that the previous version had no such bound at all.
        for model, region in combos:
            if (model, region) in tried:
                continue
            tried.add((model, region))
            self.last_model, self.last_region = model, region
            # Deliberately NOT a `with ThreadPoolExecutor(...) as executor:` block:
            # the context manager's __exit__ calls shutdown(wait=True), which would
            # block until the submitted call finishes even after our own timeout
            # fires below - silently defeating the entire point of this timeout.
            # shutdown(wait=False) lets us move on immediately; a hung call is
            # abandoned (Python cannot forcibly kill a thread) rather than blocking
            # the request that's waiting on an answer.
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            started = time.monotonic()
            try:
                future = executor.submit(_call_once, model, region)
                response = future.result(timeout=ATTEMPT_TIMEOUT_SECONDS)
                self.success_model, self.success_region = model, region
                self.attempts.append(
                    {"model": model, "region": region, "outcome": "success", "elapsed_s": round(time.monotonic() - started, 1)}
                )
                _WORKING_COMBO = (model, region)
                return response
            except concurrent.futures.TimeoutError as exc:
                last_exc = exc
                elapsed = round(time.monotonic() - started, 1)
                self.attempts.append(
                    {"model": model, "region": region, "outcome": "client_timeout", "elapsed_s": elapsed}
                )
                logger.warning(
                    "Grounded generation TIMED OUT after %ss (model=%s, region=%s).",
                    ATTEMPT_TIMEOUT_SECONDS, model, region,
                )
            except Exception as exc:  # noqa: BLE001 - try the next model/region
                last_exc = exc
                elapsed = round(time.monotonic() - started, 1)
                self.attempts.append(
                    {
                        "model": model,
                        "region": region,
                        "outcome": "error",
                        "elapsed_s": elapsed,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc)[:300],
                    }
                )
                logger.warning(
                    "Grounded generation failed (model=%s, region=%s).", model, region, exc_info=True
                )
            finally:
                executor.shutdown(wait=False)
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("No grounding model/region available.")


def _get_grounded_model():
    return _GroundedModel()


def _collect_citations(response) -> list[str]:
    """Best-effort extraction of the real source URLs the grounded search used.
    Grounding metadata shape varies across SDK versions, so this is defensive.

    Primary shape (google-genai): ``response.candidates[i].grounding_metadata
    .grounding_chunks[j].web.uri``. We also defensively scan ``grounding_supports``
    for any nested web URIs so a slightly different SDK shape still yields
    citations rather than silently returning none."""
    urls: list[str] = []

    def _add(uri) -> None:
        if isinstance(uri, str) and uri and uri not in urls:
            urls.append(uri)

    try:
        for candidate in getattr(response, "candidates", []) or []:
            meta = getattr(candidate, "grounding_metadata", None)
            if not meta:
                continue
            # Primary: grounding_chunks[].web.uri
            for chunk in getattr(meta, "grounding_chunks", []) or []:
                web = getattr(chunk, "web", None)
                _add(getattr(web, "uri", None) if web else None)
            # Defensive: grounding_supports[] may carry nested web references
            # in some SDK builds; pull any uri we can find without raising.
            for support in getattr(meta, "grounding_supports", []) or []:
                web = getattr(support, "web", None)
                _add(getattr(web, "uri", None) if web else None)
    except Exception:  # noqa: BLE001 - citation extraction must never break discovery
        logger.warning("Could not extract grounding citations.", exc_info=True)
    return urls


def diagnose_discovery(sector: str = "cross-border payments") -> dict:
    """Attempt ONE real grounded generation and return a structured, SAFE
    diagnostic that SURFACES the real error instead of swallowing it.

    Unlike ``discover_startups`` (which degrades gracefully to a reason string),
    this reports exactly what happened: which region succeeded, or the type and
    (truncated) message of the last failure. It NEVER raises and NEVER includes
    credentials or tokens — only the exception type/message and a short preview
    of the model text.

    Returns a dict of the shape::

        {
          "ok": bool,
          "region": str | None,          # region that succeeded, else None
          "model": str,                  # model name attempted
          "error_type": str | None,      # exception class name of last failure
          "error_message": str | None,   # truncated to 500 chars
          "has_text": bool,              # model returned non-empty text
          "num_citations": int,          # grounding citations extracted
          "raw_preview": str | None,     # first 300 chars of model text
        }
    """
    result: dict = {
        "ok": False,
        "region": None,
        "model": _MODEL_NAME,
        "model_used": None,
        "error_type": None,
        "error_message": None,
        "has_text": False,
        "num_citations": 0,
        "raw_preview": None,
        "attempts": [],
    }

    # Obtain the grounded model through the same factory discover_startups uses,
    # so this diagnostic exercises (and tests can stub) exactly that seam.
    try:
        model = _get_grounded_model()
    except Exception as exc:  # noqa: BLE001 - init/env issues must be reported, not raised
        result["error_type"] = type(exc).__name__
        result["error_message"] = str(exc)[:500]
        return result

    prompt = _DISCOVERY_PROMPT_TEMPLATE.format(
        n=1, sector=(sector or "").strip() or "cross-border payments"
    )
    try:
        response = model.generate_content(prompt)
    except Exception as exc:  # noqa: BLE001 - SURFACE the real (last) failure, never raise
        result["region"] = getattr(model, "last_region", None)
        result["model_used"] = getattr(model, "last_model", None)
        result["error_type"] = type(exc).__name__
        result["error_message"] = str(exc)[:500]
        result["attempts"] = getattr(model, "attempts", [])
        return result

    text = (getattr(response, "text", None) or "").strip()
    citations = _collect_citations(response)
    result.update(
        ok=True,
        region=getattr(model, "success_region", None),
        model_used=getattr(model, "success_model", None),
        has_text=bool(text),
        num_citations=len(citations),
        raw_preview=text[:300] if text else None,
        attempts=getattr(model, "attempts", []),
    )
    return result


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
    except Exception as e:  # noqa: BLE001
        logger.warning("Discovery failed during model call.", exc_info=True)
        # Surface a short, safe form of the real exception so the failure is
        # debuggable while still degrading gracefully (no credentials leaked).
        return [], f"Live discovery call failed: {type(e).__name__}: {str(e)[:160]}"

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
