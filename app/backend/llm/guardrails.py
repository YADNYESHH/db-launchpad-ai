"""Doc §23.4 'what not to claim' / §24.4 conduct guardrails.

Scans any LLM-generated (or template) text for language that would turn
decision support into an implied guarantee, suitability statement, or regulated
advice.

The detector is deterministic and network-free — no model, no external call —
so every flag is fully explainable and reproducible. It works in three layers,
cheapest first:

1. Normalization: lowercase, strip punctuation, collapse whitespace, and apply
   light stemming to a handful of high-signal tokens (guarantee/guaranteed,
   assure/assured, approve/approved, qualify/qualifies, ...). This lets a single
   rule generalize across inflections without a stemmer dependency.
2. Exact banned-phrase matching against ``BANNED_PHRASES`` (unchanged floor).
3. Compiled intent regexes that capture the *semantic categories* the banned
   phrases represent, so paraphrases that dodge every literal phrase are still
   caught (e.g. "we guarantee you'll get approved", "assured returns of 8%").

The regexes are intentionally conservative: they require a claim verb near a
claim object (approval, returns, suitability, ...) rather than firing on any
mention of "investment" or "compliant" in isolation, to keep zero false
positives on legitimate relationship-manager prose.
"""

import re

from ..models.recommendation import BANNED_PHRASES

# --- Layer 1: normalization ------------------------------------------------

_PUNCT_RE = re.compile(r"[^a-z0-9%]+")
_WS_RE = re.compile(r"\s+")

# Light, targeted stemming: collapse the inflected forms of a few high-signal
# tokens to a single stem so intent rules can match "guarantee", "guaranteed",
# and "guarantees" with one pattern. Applied only to the copy of the text used
# by the intent regexes (layer 3); exact phrase matching (layer 2) runs on the
# un-stemmed normalized text so its reported phrase stays faithful.
_STEM_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bguarante\w*"), "guarantee"),
    (re.compile(r"\bguarantie\w*"), "guarantee"),
    (re.compile(r"\bassur\w*"), "assure"),
    (re.compile(r"\bensur\w*"), "ensure"),
    (re.compile(r"\bpromis\w*"), "promise"),
    (re.compile(r"\bapprov\w*"), "approve"),
    (re.compile(r"\bqualif\w*"), "qualify"),
    (re.compile(r"\beligib\w*"), "eligible"),
    (re.compile(r"\bcertain\w*"), "certain"),
]


def _normalize(text: str) -> str:
    """Lowercase, drop punctuation, and collapse whitespace to single spaces."""
    lowered = text.lower()
    despunct = _PUNCT_RE.sub(" ", lowered)
    return _WS_RE.sub(" ", despunct).strip()


def _stem(normalized: str) -> str:
    stemmed = normalized
    for pattern, repl in _STEM_RULES:
        stemmed = pattern.sub(repl, stemmed)
    return stemmed


# --- Layer 3: semantic intent patterns -------------------------------------

# Each entry is (human-readable flag, [compiled patterns]). Patterns run against
# the *stemmed* normalized text. If any pattern matches, the flag is emitted
# once. Distances between claim verb and claim object are bounded (``{0,N}``) so
# the rules stay local and conservative.
_INTENT_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    (
        "intent:guaranteed_outcome",
        [
            re.compile(
                r"\b(guarantee|assure|ensure|promise)\b[\w ]{0,40}"
                r"\b(return|returns|profit|profits|save|saving|savings|approve|"
                r"qualify|result|results|gain|gains|yield|yields|success|rate|rates)\b"
            ),
            re.compile(
                r"\b(return|returns|profit|profits|approve|qualify|result|results|"
                r"gain|gains|rate|rates|outcome)\b[\w ]{0,25}"
                r"\b(guarantee|assure|ensure|promise)\b"
            ),
        ],
    ),
    (
        "intent:assured_returns",
        [
            re.compile(
                r"\b(assure|guarantee|promise|lock in|locked in)\b[\w ]{0,25}"
                r"\b(return|returns|profit|profits|yield|yields|gain|gains)\b"
            ),
            re.compile(r"\b(return|returns|yield|yields)\b[\w ]{0,10}\bof\b[\w ]{0,10}\d+\s*%"),
        ],
    ),
    (
        "intent:approval_certainty",
        [
            re.compile(
                r"\b(definitely|certainly|surely|certain|guarantee|assure|100 %|"
                r"without a doubt|no doubt|for sure)\b[\w ]{0,30}"
                r"\b(approve|qualify|accept|accepted|eligible)\b"
            ),
            re.compile(
                r"\b(approve|qualify|accept|eligible)\b[\w ]{0,20}"
                r"\b(guarantee|for sure|no doubt|without a doubt|certain)\b"
            ),
        ],
    ),
    (
        "intent:risk_free",
        [
            re.compile(
                r"\b(risk free|no risk|zero risk|without any risk|without risk|"
                r"cannot lose|can t lose|nothing to lose|no downside)\b"
            )
        ],
    ),
    (
        "intent:financial_advice",
        [
            re.compile(r"\b(financial|investment|tax)\s+advice\b"),
            re.compile(r"\byou should invest\b"),
            re.compile(r"\bwe (would )?recommend (that )?(you )?invest\b"),
            re.compile(r"\b(our|my) advice (is )?to\b"),
            re.compile(r"\byou ought to invest\b"),
        ],
    ),
    (
        "intent:suitability_claim",
        [
            re.compile(
                r"\b(perfect|ideal|best|great|right)\s+"
                r"(fit|match|choice|option|product|solution)\s+for\s+"
                r"(you|this client|this customer|them|your needs)\b"
            ),
            re.compile(r"\bsuitable for\b"),
            re.compile(r"\bexactly what (you|this client|they) need\b"),
        ],
    ),
    (
        "intent:regulatory_promise",
        [
            re.compile(
                r"\b(fully compliant|regulator approved|regulatory approval|"
                r"guaranteed compliance|compliant with all|meets all regulatory|"
                r"regulatory sign off|regulator backed)\b"
            )
        ],
    ),
    (
        "intent:best_rates_guaranteed",
        [
            re.compile(r"\bbest\b[\w ]{0,15}\brates?\b[\w ]{0,10}\bguarantee\b"),
            re.compile(r"\bguarantee\b[\w ]{0,10}\bbest\b[\w ]{0,10}\brates?\b"),
        ],
    ),
]


def scan_for_banned_phrases(text: str) -> list[str]:
    """Return a de-duplicated list of guardrail flags for ``text``.

    Flags are either an exact banned phrase from ``BANNED_PHRASES`` or a
    human-readable ``intent:<category>`` label from the semantic rules. An empty
    list means the text is clean. The function name and ``list[str]`` contract
    are unchanged so existing callers keep working.
    """
    if not text:
        return []

    normalized = _normalize(text)
    stemmed = _stem(normalized)

    flags: list[str] = []
    seen: set[str] = set()

    def _add(flag: str) -> None:
        if flag not in seen:
            seen.add(flag)
            flags.append(flag)

    # Layer 2: exact banned-phrase matching. Normalize each phrase the same way
    # so hyphenation/spacing differences (e.g. "risk-free" vs "risk free") match.
    for phrase in BANNED_PHRASES:
        if _normalize(phrase) in normalized:
            _add(phrase)

    # Layer 3: semantic intent patterns.
    for flag, patterns in _INTENT_RULES:
        if any(pattern.search(stemmed) for pattern in patterns):
            _add(flag)

    return flags
