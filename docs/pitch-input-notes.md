# Pitch input notes — feed into pitch/video creation

Concrete lines and talking points to pull from, based on the current build and the hackathon-
criteria review (`docs/reviews/hackathon-criteria-review.md`). Written to be copy-pasteable into
narration, not a full script — that's owned by the pitch/video session.

Terminology: say **"hackathon evaluation criteria"** when referring to judging; **"Decathlon"**
only when referring to the product's own 10-dimension digital-twin score.

## The 30-second wow moment
"Type a sector. Watch it discover real, currently-operating startups via live web search, score
them across ten business dimensions, rank them, and produce a governed relationship-manager brief
— with every fact traced to a real source, and nothing released to a client without a human
signing off first."

## Framing correction (say this early, don't let a judge find it first)
"This is a governed discovery, scoring, and advisory workflow — not a claim that AI autonomously
discovers and ranks the world's startups. The discovery layer is real and live; the scoring engine
is deterministic and explainable; the one place we use a language model for prose is guarded and
falls back safely if it's ever unavailable."

## Numbers worth saying out loud
- 132+ automated tests, ruff-clean, CI with linting + dependency scanning + secret scanning.
- Three real production bugs found and fixed live during this build (a Firestore data-modeling
  bug, a missing database index, a deployment scripting bug) — evidence of real engineering rigor,
  not a slide-only claim.
- 100% audit coverage: every score, recommendation, approval, discovery, and weight change is
  logged with who did it and when.
- Indicative EUR pipeline-value estimate per startup and portfolio-wide — turns a 0–100 score into
  a number a business leader actually reasons about.

## The trust story (the app's strongest dimension — lean on this)
- Every score shows its rationale and its confidence — never an unexplained number.
- Missing data is never silently treated as zero; it blocks a false "high priority" call.
- A recommendation cannot reach a client without a named human approving it first.
- Every discovered fact carries the real source URL that supports it.
- Synthetic vs. live data is labeled everywhere, always.

## Honest limitations to name proactively (credibility move, not a weakness to hide)
- Fairness/bias of the discovery mechanism is untested — search-grounded discovery will skew
  toward startups with strong English-language web presence. Name this as a known next step.
- Only 1 of ~9 identified banking-opportunity types is scored today (cross-border payments).
  Framed as "the hero use case, proven end to end," not "the whole product."
- No enterprise SSO/CRM integration yet — this is a governed prototype, not wired into a bank's
  existing identity or client systems.
- Pipeline-value figures are indicative estimates, not validated against real deal outcomes.

## One-line answers if a judge asks directly
- "Is this agentic AI?" → "One narrow, guarded, fallback-safe LLM call for prose, plus one
  live-grounded search agent for discovery. We chose fewer, well-understood components over an
  agent graph, because a bank's model-risk function will trust that more."
- "Is this real data?" → "Discovery is genuinely live — real companies, real citations. Everything
  else is synthetic by design, clearly labeled, because that's the responsible way to demo before
  any real client data is involved."
- "Why should a bank trust the score?" → "Because it can't hide from you — every driver, every
  weight, every piece of evidence is visible, and a human has to sign off before anything reaches
  a client."

## Where the new RM-chat feature fits in the narration (if it lands before recording)
Slot it right after the RM-brief approval beat: "And if the RM has a follow-up question the brief
didn't answer, they just ask — right on the startup's page, answered from what the system already
knows, verified live where possible, and saved automatically to that startup's record."
