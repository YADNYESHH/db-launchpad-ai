"""Tests for the RM doubt-resolution chat orchestrator (orchestrator/chat.py):
the grounded-or-fallback answer contract, the guardrail defense-in-depth,
chat history persistence/ordering, and citation-driven auto-enrichment.

Follows the same monkeypatch idiom as test_discovery.py (lines ~110-135):
stub the grounded model factory so no real network/LLM call happens.
"""
from types import SimpleNamespace

import pytest

from ..orchestrator import chat as _chat
from ..orchestrator.chat import answer_startup_question
from ..orchestrator.pipeline import NotFoundError
from ..seed.data import NOVATRADE_ID, NOVATRADE_PROFILE
from ..store.memory import InMemoryStore


def _fake_response(text: str, uris: list[str] | None = None):
    chunks = [SimpleNamespace(web=SimpleNamespace(uri=u)) for u in (uris or [])]
    candidate = SimpleNamespace(grounding_metadata=SimpleNamespace(grounding_chunks=chunks))
    return SimpleNamespace(text=text, candidates=[candidate])


def _patch_model(monkeypatch, response=None, raise_exc=None):
    if raise_exc is not None:

        def _boom(_prompt):
            raise raise_exc

        stub = SimpleNamespace(generate_content=_boom)
    else:
        stub = SimpleNamespace(generate_content=lambda _prompt: response)
    # chat.py does `from ..discovery.agent import _get_grounded_model`, which
    # binds the name in chat.py's own module namespace at import time.
    # Patching discovery.agent._get_grounded_model does NOT affect that
    # already-bound reference (verified: doing so leaves the real function in
    # place and the stub call is never reached) - patch the name where it is
    # used instead, per the standard mock.patch gotcha.
    monkeypatch.setattr(_chat, "_get_grounded_model", lambda: stub)


@pytest.fixture
def store() -> InMemoryStore:
    # NOVATRADE_PROFILE is a shared module-level singleton reused across the
    # whole test suite, and answer_startup_question's auto-enrichment step
    # mutates profile.source_citations in place. Seed a deep copy so these
    # tests never leak citation state into other test files.
    s = InMemoryStore()
    s.save_profile(NOVATRADE_PROFILE.model_copy(deep=True))
    return s


def test_answer_startup_question_raises_not_found_for_unknown_startup(store):
    with pytest.raises(NotFoundError):
        answer_startup_question(store, "ST-DOES-NOT-EXIST", "when did they raise?", actor="rm@bank.example")


def test_fallback_path_when_grounded_call_raises(store, monkeypatch):
    _patch_model(monkeypatch, raise_exc=RuntimeError("boom"))

    _, assistant_message = answer_startup_question(store, NOVATRADE_ID, "who are their competitors?", actor="rm1")

    assert assistant_message.llm_used is False
    assert assistant_message.citations == []
    assert assistant_message.text.startswith(f"Based on current records for {NOVATRADE_PROFILE.name}")


def test_guardrail_forces_fallback_on_flagged_model_text(store, monkeypatch):
    flagged_text = "We guarantee you will get approved for this credit line."
    _patch_model(monkeypatch, response=_fake_response(flagged_text))

    _, assistant_message = answer_startup_question(store, NOVATRADE_ID, "will they get approved?", actor="rm1")

    assert assistant_message.text != flagged_text
    assert assistant_message.llm_used is False
    assert assistant_message.citations == []
    # The flagged path force-downgrades to the never-flagged fallback answer,
    # so the final message carries no guardrail_flags (defense-in-depth clears them).
    assert assistant_message.guardrail_flags == []


def test_success_path_uses_grounded_answer_and_citations(store, monkeypatch):
    citation = "https://example.com/novatrade-news"
    _patch_model(monkeypatch, response=_fake_response("They recently entered the UK market.", uris=[citation]))

    _, assistant_message = answer_startup_question(store, NOVATRADE_ID, "any recent expansion?", actor="rm1")

    assert assistant_message.llm_used is True
    assert citation in assistant_message.citations
    assert assistant_message.text == "They recently entered the UK market."


def test_auto_enrichment_adds_new_citation_and_logs_event(store, monkeypatch):
    assert NOVATRADE_PROFILE.source_citations == []
    citation = "https://example.com/new-source"
    _patch_model(monkeypatch, response=_fake_response("Answer text.", uris=[citation]))

    answer_startup_question(store, NOVATRADE_ID, "what's new?", actor="rm1")

    updated_profile = store.get_profile(NOVATRADE_ID)
    assert citation in updated_profile.source_citations

    enrichment_events = [e for e in store.get_audit_trail(NOVATRADE_ID) if e.event_type == "signal_auto_enriched"]
    assert len(enrichment_events) == 1
    assert enrichment_events[0].payload["new_citations"] == [citation]


def test_no_auto_enrichment_when_citation_already_on_file(store, monkeypatch):
    existing_citation = "https://example.com/already-known"
    profile = store.get_profile(NOVATRADE_ID)
    profile.source_citations.append(existing_citation)
    store.save_profile(profile)

    _patch_model(monkeypatch, response=_fake_response("Answer text.", uris=[existing_citation]))

    answer_startup_question(store, NOVATRADE_ID, "what's new?", actor="rm1")

    enrichment_events = [e for e in store.get_audit_trail(NOVATRADE_ID) if e.event_type == "signal_auto_enriched"]
    assert enrichment_events == []


def test_chat_history_records_two_exchanges_in_chronological_order(store, monkeypatch):
    _patch_model(monkeypatch, raise_exc=RuntimeError("boom"))

    answer_startup_question(store, NOVATRADE_ID, "first question?", actor="rm1")
    answer_startup_question(store, NOVATRADE_ID, "second question?", actor="rm1")

    history = store.get_chat_history(NOVATRADE_ID)
    assert len(history) == 4
    assert [m.role for m in history] == ["rm", "assistant", "rm", "assistant"]
    assert history[0].text == "first question?"
    assert history[2].text == "second question?"


def test_rm_question_answered_audit_event_logged(store, monkeypatch):
    _patch_model(monkeypatch, raise_exc=RuntimeError("boom"))

    answer_startup_question(store, NOVATRADE_ID, "any doubts?", actor="rm1")

    events = [e for e in store.get_audit_trail(NOVATRADE_ID) if e.event_type == "rm_question_answered"]
    assert len(events) == 1
    assert events[0].startup_id == NOVATRADE_ID
