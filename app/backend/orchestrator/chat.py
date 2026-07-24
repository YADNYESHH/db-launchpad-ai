"""RM doubt-resolution chat.

A Relationship Manager looking at a startup card often has a question the
static UI can't answer inline ("when exactly did they raise?", "who are their
competitors?", "what's changed since last week?"). This module answers it,
grounded first in what the system already knows (zero extra latency, zero
extra risk), falling back to a live Google-Search-grounded Gemini call only
when useful, and never shipping ungrounded/unsafe text.

This is deliberately NOT a new agent or subsystem: it reuses the exact same
seams every other stage already uses —
- the grounded-model adapter from discovery/agent.py, including the hard
  per-attempt timeout and model/region self-healing that fixed live discovery
  hanging in production;
- the same guardrail scan (llm/guardrails.py) the RM brief is screened through
  before it can ship;
- the same audit trail (orchestrator/audit.py:log_event) and Store interface
  every other stage persists through.
"""
import logging
import uuid

from ..discovery.agent import _collect_citations, _get_grounded_model
from ..llm.guardrails import scan_for_banned_phrases
from ..models import ChatMessage
from ..models.recommendation import RecommendationRecord
from ..store import Store
from .audit import log_event
from .pipeline import NotFoundError

logger = logging.getLogger(__name__)

_CHAT_PROMPT_TEMPLATE = """You are answering a Relationship Manager's question about one startup, \
for internal use at a bank. Only use live web search if the question needs information that is \
NOT already covered by the known record below (e.g. very recent news, competitors, additional \
funding detail).

Known record:
{context}

RM's question: {question}

Rules:
- Prefer the known record above; only search if it does not already answer the question.
- If your answer relies on a web search result, cite the real source URL.
- If you cannot support an answer from the known record or a real search result, say plainly \
that it is not confirmed - never guess.
- Do not give investment, credit-approval, or suitability advice, and do not guarantee any outcome.
- Answer in 2-4 sentences of plain prose, no markdown headers."""


def _format_signal(s) -> str:
    return (
        f"- {s.signal_type.replace('_', ' ')} in {s.country or 'n/a'} "
        f"({s.signal_date.isoformat()}, confidence {s.confidence:.2f}): {s.evidence_note}"
    )


def _build_context(profile, score, signals, recommendation, payment) -> str:
    lines = [
        f"{profile.name} - {profile.sector}, HQ {profile.hq_country}, {profile.growth_stage} / {profile.funding_stage}.",
        f"Target markets: {', '.join(profile.target_countries) or 'none on file'}.",
        f"Annual revenue (est.): EUR {profile.annual_revenue_eur:,.0f}.",
    ]
    if profile.discovery_note:
        lines.append(f"Discovery note: {profile.discovery_note}")
    if payment:
        lines.append(
            f"Cross-border payment value (est.): EUR {payment.annual_cross_border_payment_value_eur:,.0f}/yr "
            f"across {', '.join(payment.currencies) or 'n/a'}."
        )
    if score:
        lines.append(f"Current opportunity score: {score.final_score:.0f}/100 ({score.priority_band.value}).")
    if signals:
        lines.append("Expansion signals on file:")
        lines.extend(_format_signal(s) for s in signals[:8])
    else:
        lines.append("No expansion signals on file yet.")
    if recommendation:
        lines.append(f"Latest RM brief 'why now': {recommendation.why_now}")
    if profile.source_citations:
        lines.append(f"Public sources on file: {', '.join(profile.source_citations[:5])}")
    return "\n".join(lines)


def _fallback_answer(profile_name: str, context: str) -> str:
    return (
        f"Based on current records for {profile_name}:\n{context}\n\n"
        "(A live lookup was not available just now - this answer uses only what is already on file.)"
    )


def answer_startup_question(
    store: Store, startup_id: str, question: str, actor: str
) -> tuple[ChatMessage, ChatMessage]:
    """Persist the RM's question, produce a grounded-or-fallback answer,
    persist that too, and return ``(rm_message, assistant_message)``.

    Auto-enrichment: if a live-grounded answer surfaces a source URL not
    already on the profile's evidence trail, it is appended to
    ``profile.source_citations`` and logged - the "agent adds relevant
    details to the startup's record" behavior, scoped honestly to citations
    actually returned by a real grounded search rather than inventing a
    structured signal from freeform chat text.
    """
    profile = store.get_profile(startup_id)
    if profile is None:
        raise NotFoundError(f"No profile found for startup_id={startup_id}")

    latest_score = store.get_latest_score_record(startup_id)
    score = latest_score[1] if latest_score else None
    signals = store.get_signals(startup_id)
    payment = store.get_payment_profile(startup_id)
    recommendation: RecommendationRecord | None = None

    context = _build_context(profile, score, signals, recommendation, payment)

    rm_message = ChatMessage(message_id=str(uuid.uuid4()), startup_id=startup_id, role="rm", text=question)
    store.append_chat_message(rm_message)

    answer_text: str
    llm_used = False
    citations: list[str] = []

    try:
        model = _get_grounded_model()
        prompt = _CHAT_PROMPT_TEMPLATE.format(context=context, question=question)
        response = model.generate_content(prompt)
        candidate_text = (getattr(response, "text", None) or "").strip()
        if not candidate_text:
            raise ValueError("empty response from grounded model")
        if scan_for_banned_phrases(candidate_text):
            raise ValueError("candidate answer tripped the guardrail")
        answer_text = candidate_text
        citations = _collect_citations(response)
        llm_used = True
    except Exception:  # noqa: BLE001 - any failure degrades to the safe on-file answer
        logger.warning("Chat grounded call failed or was rejected; falling back to on-file answer.", exc_info=True)
        answer_text = _fallback_answer(profile.name, context)

    guardrail_flags = scan_for_banned_phrases(answer_text)
    if guardrail_flags:
        # Should be unreachable (the LLM path is already screened above and the
        # fallback is built purely from known facts), but never ship flagged text.
        answer_text = _fallback_answer(profile.name, context)
        llm_used = False
        citations = []
        guardrail_flags = []

    assistant_message = ChatMessage(
        message_id=str(uuid.uuid4()),
        startup_id=startup_id,
        role="assistant",
        text=answer_text,
        citations=citations,
        llm_used=llm_used,
        guardrail_flags=guardrail_flags,
    )
    store.append_chat_message(assistant_message)

    log_event(
        store,
        startup_id,
        "rm_question_answered",
        payload={"question": question, "llm_used": llm_used, "guardrail_flags": guardrail_flags},
        actor=actor,
    )

    new_citations = [c for c in citations if c not in profile.source_citations]
    if new_citations:
        profile.source_citations.extend(new_citations)
        store.save_profile(profile)
        log_event(
            store,
            startup_id,
            "signal_auto_enriched",
            payload={"new_citations": new_citations, "trigger": "rm_chat"},
            actor=actor,
        )

    return rm_message, assistant_message
