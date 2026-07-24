# DB LaunchPad AI — 5-Minute Pitch & Demo Narration

**Team:** toruk-makto · **Event:** 2026 Deutsche Bank Global Hackathon ("The Decathlon")
**Runtime target:** 4 min 45 sec (hard stop < 5:00)
**Two narrators:** 🎙️ **ARIA (female)** covers the first half (hook → live demo → how it works). 🎙️ **ETHAN (male)** covers the second half (architecture → responsible AI → value → close).
**Voice direction (both):** warm, confident, unhurried, softly-spoken but energised. Smile while speaking. Land each key phrase, then a short beat. Vary pace: slow on the vision lines, brisk on feature lists.

> Recording tip: use the companion `demo_walkthrough.py` to drive the app on screen while these lines are read. Slide numbers refer to `pitch/index.html`.

---

## PART 1 — ARIA (female) · 0:00 – 2:20

### Slide 1 · Title (0:00–0:20)
**[Tone: warm, slow, inviting. A gentle smile.]**
"What if a relationship manager could call the *right* client, at exactly the *right* moment, with a reason they can *prove* — **before the competition even notices?**
_(beat)_ That's **DB LaunchPad AI**. And it's live."

### Slide 2 · The problem (0:20–0:50)
**[Tone: empathetic, slightly urgent.]**
"Today, banks react late. A scale-up opens three new countries, hires abroad, raises a round — and that buying signal is *public* for days before the bank hears it.
Relationship managers are drowning in hundreds of names, with no way to triage and no defensible reason why one prospect matters more than another.
_(beat, drop pace)_ The intelligence exists. The *timely, explainable, actionable* intelligence does not — **so we built it.**"

### Slide 3 · The idea (0:50–1:15)
**[Tone: bright, hopeful — this is the turn.]**
"DB LaunchPad AI moves the bank from *reactive* to *proactive*. It continuously **discovers** high-growth companies expanding across borders, builds a **digital twin** of each, **scores the opportunity** with transparent AI, quantifies the **euro value**, and hands the RM an **approved, evidence-backed brief**.
_(beat)_ And it's decision *support* — never autonomous. A human approves every single output."

### Slide 4 → LIVE DEMO (1:15–2:20)
**[Tone: confident, conversational — you're showing, not telling. Slow down; let the screen breathe.]**
"Let me show you — this is running on Google Cloud, right now."
- **[Login as Relationship Manager]** "I sign in as a relationship manager. Notice the governance front-and-centre — human-in-the-loop, explainable, no fabricated data, audit-logged."
- **[Portfolio]** "Here's my portfolio, *ranked* by opportunity — and I can see the total indicative pipeline value across it at a glance. Green is act-now, down to grey for hold."
- **[Open the top company → Twin & value tab]** "I open the top opportunity. This is our **Decathlon digital twin** — ten business dimensions of maturity — and an **indicative euro value** with a transparent breakdown. Notice the agent pipeline: it honestly tells me whether this came from live grounded search or seed data."
- **[Scorecard]** "The scorecard is fully explainable — seven factors, each with weight, evidence and rationale. Where data is missing, the band is *capped* — honesty by design."
- **[RM brief]** "One click generates the RM brief — and a guardrail strips any over-claim before a human approves it. Every step lands in the audit trail."
_(beat, hand over)_ "So that's the experience. My colleague will show you *how* it's engineered — and why a bank can trust it."

---

## PART 2 — ETHAN (male) · 2:20 – 4:45

### Slide 5 · How it works (2:20–2:55)
**[Tone: assured, precise, proud of the craft.]**
"Thank you, Aria. Under the hood, DB LaunchPad AI is a **team of agents**: discovery, a digital-twin builder, the Decathlon, opportunity scoring, recommendation with a guardrail, human approval, and audit.
Two design choices make it bank-grade: discovery is **grounded** — Gemini plus Google Search, with real citations and GLEIF registry verification. And the score is **deterministic** — a transparent weighted model, reproducible every run. The language model only phrases prose; **it never moves a number.**"

### Slide 6 · Technology (2:55–3:25)
**[Tone: crisp, fast on the stack, then slow to land the trust line.]**
"The stack is enterprise-grade and *live today*: FastAPI, React, grounded Gemini 2.5, Firestore, all on Cloud Run — deployed through GitHub Actions with tests, lint, secret and dependency scanning on every push.
Authentication is role-based; there are **no stored service-account keys** — we use Workload Identity Federation. And it's backed by **132 automated tests**.
_(beat)_ We separated the deterministic score from the generative narrative on purpose — so the bank can *trust the number* and still get fluent prose."

### Slide 7 · Responsible AI (3:25–3:55)
**[Tone: sincere, values-led — slow and deliberate.]**
"For a bank, **trust is the product**. So fairness, transparency, accountability and auditability are *architected in*, not bolted on.
Human-in-the-loop on every recommendation. Explainable scores with visible drivers. No fabricated data — grounded facts with citations, and private data left honestly absent. Guardrails that block over-claims, governed scoring weights, and a full audit trail on every action."

### Slide 8 · Business value (3:55–4:15)
**[Tone: business-leader confidence.]**
"The value is measurable. We quantify **indicative annual revenue** per company and across the portfolio — FX, cash-management fees and deposit income. RMs stop triaging noise and act on a ranked, evidence-backed shortlist. And it's one engine that generalises across every sector and every European corridor."

### Slides 9–11 · Decathlon, criteria & close (4:15–4:45)
**[Tone: build to a warm, memorable finish. Slow the last line right down.]**
"Our ten-dimension twin is a deliberate tribute to the Decathlon — form and substance aligned. It maps directly to every judging axis: strategic value, robust scalable architecture, genuine innovation, and a user-first experience RMs will actually adopt.
_(beat)_ Everything you saw is **built, tested, and live** — with a clear roadmap ahead.
_(slow, land it)_ DB LaunchPad AI: **grounded, explainable, governed, and live** — from a public signal to a defensible action, with an audit trail behind every number. _(beat)_ Thank you."

---

## MULTI-ROLE REVIEW — how this pitch was pressure-tested

I rewrote and stress-tested the pitch through five judge lenses; the version above is the synthesis.

| Lens | What they care about | What we made sure lands |
|---|---|---|
| **CEO / Business leader** | Revenue, strategic fit, speed to value | Opening hook = revenue-before-competition; quantified € pipeline value; "reactive → proactive" framing; on-theme Decathlon. |
| **CTO / Technologist** | Real engineering, not a mock | 132 tests, CI/CD, deterministic-vs-LLM separation, grounded Gemini, WIF, "LLM never moves a number." |
| **Solution architect** | Robust, secure, scalable, compliant | Cloud Run + Firestore + RBAC + audit + no stored keys; generalises across sectors/corridors; deployment governance. |
| **Product owner** | Adoption, UX, user need | RM-first workflow, "3 clicks to score", ranked portfolio, compare, trust-building transparency. |
| **Engineer** | Correctness, honesty | Missing-data caps, corroboration, guardrails, honest provenance ("live vs seed"), graceful fallback. |
| **Startup owner (the client)** | Fairness, no creepy fabrication | "No fabricated data", citations, human approval — the bank earns trust rather than assuming it. |

**Delivery techniques baked in:** a provocative one-line hook; problem→turn→proof structure; a live demo in the first half (show, don't tell); concrete numbers over adjectives; a two-voice hand-off for pace variety; and a slow, memorable closing line ("grounded, explainable, governed, live").

---

## APPENDIX — extended Q&A (if judges probe)

- **"How current is the live data?"** Discovery runs grounded web search on demand; results carry the real source URLs used. If grounding is briefly unavailable, the app degrades gracefully and says so — it never fabricates.
- **"What stops a wrong recommendation reaching a client?"** Three gates: deterministic scoring, a banned-claim guardrail, and mandatory human approval — all audit-logged.
- **"Regulatory / data protection?"** No confidential client data in the prototype; RBAC + audit + WIF; scoring changes are governed (proposed by product owners, activated by admins).
- **"Why Gemini + Google Search grounding?"** It gives real, citable public evidence with minimal infra, and cleanly separates *facts* (grounded) from *phrasing* (LLM) from *decisions* (deterministic).
- **"Biggest technical risk and how you handled it?"** Model/region availability — we made the discovery agent self-heal across candidate models and regions, with graceful synthetic fallback so a demo never breaks.
- **"What would you build next with a quarter?"** More opportunity types, an outcome learning loop to tune weights, CRM/core-banking connectors, and observability.
