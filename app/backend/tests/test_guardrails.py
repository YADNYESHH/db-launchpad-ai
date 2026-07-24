"""Tests for the conduct guardrail scanner (llm/guardrails.py).

Three concerns:
  (a) every literal banned phrase is still flagged (backward-compatible floor);
  (b) paraphrased violations that dodge the literal phrases are now caught by
      the semantic intent layer;
  (c) legitimate relationship-manager prose produces zero flags.
"""

import pytest

from ..llm.guardrails import scan_for_banned_phrases
from ..models.recommendation import BANNED_PHRASES

# --- (a) existing banned phrases still flagged ------------------------------

@pytest.mark.parametrize("phrase", BANNED_PHRASES)
def test_every_banned_phrase_is_still_flagged(phrase: str):
    # Directly and embedded in a sentence, the exact phrase must be caught.
    assert scan_for_banned_phrases(phrase), f"phrase not flagged: {phrase!r}"
    sentence = f"For this client, {phrase} in the near term."
    assert scan_for_banned_phrases(sentence), f"phrase not flagged in context: {phrase!r}"


def test_hyphen_and_spacing_variants_match_same_phrase():
    # "risk-free" (banned) should also match the spaced form "risk free".
    assert scan_for_banned_phrases("this is a risk free option")
    assert scan_for_banned_phrases("this is a risk-free option")


# --- (b) paraphrased violations caught by the semantic layer ----------------

PARAPHRASED_VIOLATIONS = [
    ("we guarantee you'll get approved", "intent:approval_certainty"),
    ("you will definitely qualify for this facility", "intent:approval_certainty"),
    ("assured returns of 8% every year", "intent:assured_returns"),
    ("we can lock in guaranteed returns for the client", "intent:guaranteed_outcome"),
    ("this is a risk-free investment for your capital", "intent:risk_free"),
    ("there is no downside and nothing to lose here", "intent:risk_free"),
    ("this product is a perfect fit for you", "intent:suitability_claim"),
    ("this is the ideal solution for your needs", "intent:suitability_claim"),
    ("our platform is fully compliant and regulator-approved", "intent:regulatory_promise"),
    ("best rates guaranteed on all transfers", "intent:best_rates_guaranteed"),
]


@pytest.mark.parametrize("text, expected_flag", PARAPHRASED_VIOLATIONS)
def test_paraphrased_violation_is_flagged(text: str, expected_flag: str):
    flags = scan_for_banned_phrases(text)
    assert flags, f"paraphrase not flagged at all: {text!r}"
    assert expected_flag in flags, f"expected {expected_flag} for {text!r}, got {flags}"


def test_pure_intent_paraphrase_without_any_literal_phrase():
    # Contains no literal banned phrase, yet must be flagged by intent rules.
    text = "You will definitely qualify for this facility."
    flags = scan_for_banned_phrases(text)
    assert not any(phrase in flags for phrase in BANNED_PHRASES)
    assert "intent:approval_certainty" in flags


# --- (c) clean corpus: zero false positives ---------------------------------

CLEAN_CORPUS = [
    "This startup shows strong cross-border payment growth and may benefit from treasury services.",
    "The company's FX volumes suggest a potential fit with our cash-management products.",
    "Recent funding rounds indicate the firm may scale internationally over the next year.",
    "We could explore treasury and liquidity solutions if the client expresses interest.",
    "Payment processing revenue has grown steadily, which may increase demand for settlement services.",
    "The relationship manager should confirm the client's onboarding documents before any meeting.",
    "This may be a good opportunity to discuss cross-border payment needs.",
    "Early signals point to expanding transaction volumes in the EU corridor.",
    "The startup could improve margins through better working-capital management.",
    "Consider whether the firm's growth aligns with our trade-finance offering.",
    "The client appears to have a solid compliance track record.",
    "The firm operates in the investment technology sector.",
    "Their customer growth rate has been impressive this quarter.",
]


@pytest.mark.parametrize("text", CLEAN_CORPUS)
def test_clean_sentence_has_no_flags(text: str):
    assert scan_for_banned_phrases(text) == [], f"false positive on: {text!r}"


def test_empty_text_is_clean():
    assert scan_for_banned_phrases("") == []


# --- contract sanity --------------------------------------------------------

def test_flags_are_deduplicated():
    # "guaranteed" and a guaranteed-outcome paraphrase in one string should not
    # duplicate any flag.
    text = "We guarantee guaranteed returns; assured returns are guaranteed."
    flags = scan_for_banned_phrases(text)
    assert len(flags) == len(set(flags))
