# DB LaunchPad AI — 5-Minute Pitch & Demo Narration

**Team:** toruk-makto · **Event:** 2026 Deutsche Bank Global Hackathon ("The Decathlon")
**Runtime target:** 4 min 50 sec (hard stop < 5:00)
**Two narrators:** 🎙️ **ARIA (female)** carries the first half — hook, executive value, live real companies, and the Decathlon twin (parts 1–4). 🎙️ **ETHAN (male)** carries the second half — explainable scoring, governance & architecture, responsible AI, UX, and the close (parts 5–9). Hand-off is mid-point, inside the Decathlon twin.
**Voice direction (both):** warm, confident, softly-spoken but energised, well-modulated. Smile while speaking. Land each key phrase, then a short beat. Slow on vision lines; brisk on feature lists. Every section **names the assessment criterion it proves** — say the criterion name aloud so judges hear the alignment.

> Recording tip: drive the app on screen with `demo_walkthrough.py` while these lines are read. Timestamps are cumulative and total ~4:50.

**Assessment-criteria map (say each aloud):**
1. Hook + problem → sets up the whole story · **ARIA**
2. Executive value → **Strategic vision & business value** · **ARIA**
3. Live real companies, grounded → underpins **strategic value with real evidence** · **ARIA**
4. Decathlon 10-dimension twin → **Innovation & technical excellence** · **ARIA → ETHAN (hand-off)**
5. Explainable deterministic scoring → **Transparency & explainability / responsible AI** · **ETHAN**
6. Multi-role governance + cloud → **Solution architecture, scalability, secure & compliant deployment** · **ETHAN**
7. Responsible-AI view → **Responsible & ethical AI: fairness, transparency, auditability, regulatory-safe** · **ETHAN**
8. UX & adoption → **User experience & adoption potential** · **ETHAN**
9. Roadmap + close → memorable landing · **ETHAN**

---

## PART 1 — ARIA (female) · 0:00 – 2:20

### 1 · Hook + the problem (0:00 – 0:35) · *sets up the story*
**[Tone: warm, slow, inviting — a gentle smile. Then a touch of urgency.]**
"What if a relationship manager could call the *right* company, at exactly the *right* moment, with a reason they can *prove* — **before a competitor even notices?**
_(beat)_ Today, banking is *reactive*. A scale-up opens new countries, hires abroad, raises a round — and that signal is *public* for days before the bank acts. RMs drown in hundreds of names, with no way to triage and no defensible reason why one matters more than another.
_(drop pace)_ The timing is everything — and today the bank misses it. **So we built DB LaunchPad AI. And it's live, on Google Cloud, right now.**"

### 2 · Executive view — the value at stake (0:35 – 1:05) · **Strategic vision & business value**
**[Tone: business-leader confidence; unhurried, let the number land.]**
"This is our first criterion — **strategic vision and business value** — and I'll start where a leader starts: the money.
_(beat)_ Here is the executive portfolio view. Across it, LaunchPad quantifies the **total indicative euro value at stake** — the annual revenue this pipeline represents in FX, cash-management fees and deposit income. Companies are *ranked* by opportunity, green for act-now down to grey for hold.
_(slow)_ In one glance, the bank moves from *reactive* to *proactive* — a strategic shortlist, priced, in front of the right RM."

### 3 · Live, real companies — grounded, cited (1:05 – 1:45) · *strategic value, on real evidence*
**[Tone: confident, conversational — you're showing, not telling.]**
"And this is not a mock. These are **real companies** — Airwallex, Payhawk, Modulr, Pleo, Swan, Juni, TransferMate, Ankorstore.
_(beat)_ Every profile is built by **grounded discovery** — Gemini 2.5 Flash with Google Search grounding — so each fact carries a **real citation** you can click through to the source. Where a company is private and a field is genuinely unknown, we leave it honestly absent.
_(land it)_ That's the rule the whole system obeys: **no fabricated data.** The strategic value you just saw is built on evidence a bank can defend."

### 4 · The Decathlon digital twin (1:45 – 2:20) · **Innovation & technical excellence** · *hand-off*
**[ARIA — Tone: proud, curious; this is the clever bit.]**
"Open the top opportunity, and here is our **Decathlon digital twin** — the heart of our **innovation and technical excellence**.
_(beat)_ Ten business dimensions of maturity — a tribute to the ten-event Decathlon — each with an **indicative euro value** and a transparent breakdown. The agent pipeline even tells you honestly whether this came from live grounded search or seed data.
_(warm, hand over)_ Ten dimensions, one defensible twin. My colleague Ethan will show you *why* a bank can trust the number behind it."

---

## PART 2 — ETHAN (male) · 2:20 – 4:50

### 5 · Explainable deterministic scoring (2:20 – 2:55) · **Transparency & explainability / responsible AI**
**[Tone: assured, precise, proud of the craft. Slow on the trust line.]**
"Thank you, Aria. This is our next criterion — **transparency and explainability, responsible AI by design**.
_(beat)_ The score is **deterministic**: a transparent weighted model, reproducible on every run. Each factor shows its **weight, its evidence and its rationale** — nothing hidden. A **guardrail** strips any over-claim before a human ever sees it, and where data is missing, the band is *capped* — honesty enforced in code.
_(slow, land it)_ The language model only phrases the prose. **It never moves a number.** That separation is what makes the score explainable — and trustworthy."

### 6 · Multi-role governance + cloud (2:55 – 3:35) · **Solution architecture, scalability, secure & compliant deployment**
**[Tone: crisp on the flow, deliberate on security.]**
"Next: **solution architecture, scalability, and secure, compliant deployment** — proven through governance.
_(beat)_ Watch the roles. A **Product Owner proposes** new scoring weights. An **Admin activates** them. And every change lands in an immutable **audit trail** — proposer, approver, timestamp. Four distinct roles, enforced by **role-based access control**.
_(brisk)_ It runs on **Google Cloud Run** — scales to zero, scales out on demand. There are **no stored service-account keys**; we authenticate with **Workload Identity Federation**. And it's backed by **132 automated tests** in CI.
_(land it)_ Governed changes, least-privilege access, a full audit — architecture a regulator can inspect."

### 7 · Responsible-AI view (3:35 – 4:05) · **Responsible & ethical AI: fairness, transparency, auditability, regulatory-safe**
**[Tone: sincere, values-led — slow and deliberate.]**
"For a bank, **trust is the product** — so this criterion, **responsible and ethical AI**, is architected in, not bolted on.
_(beat)_ **Provenance** on every fact, with citations. **Guardrails** that block over-claims. **Human-in-the-loop** approval on every single recommendation — the AI advises, a person decides. And because scores are explainable and every action is audited, the whole system is **fair, transparent, auditable, and regulatory-safe**.
_(slow)_ We never give regulated advice autonomously. A human owns the outcome — always."

### 8 · UX & adoption (4:05 – 4:30) · **User experience & adoption potential**
**[Tone: bright, human, confident.]**
"None of this matters if an RM won't use it — so our last criterion is **user experience and adoption**.
_(beat)_ It's **RM-first**: from portfolio to a scored, evidence-backed brief in **three clicks**. No dashboards to configure, no jargon — just a ranked shortlist and a reason to call.
_(beat)_ And when the RM has a follow-up — *"who are their competitors?"* — they just **ask**: our grounded, guardrailed, audit-logged chat answers only from real evidence, never a guess.
_(land it)_ And because every claim is grounded and every score is explained, the RM *trusts* it on day one. That's how adoption actually happens — trust, not training."

### 9 · Roadmap + close (4:30 – 4:50)
**[Tone: build to a warm, memorable finish. Slow the last line right down.]**
"Everything you saw is **built, tested, and live** today. Next: more opportunity types, an outcome loop that tunes the weights, and CRM connectors.
_(beat)_ DB LaunchPad AI — **grounded, explainable, governed, and live.** From a public signal to a defensible action, with an audit trail behind every number.
_(slow, land it)_ Thank you."

---

## MULTI-ROLE REVIEW — how this pitch was pressure-tested

The narration above is the synthesis after stress-testing through seven judge lenses.

| Lens | What they care about | What we made sure lands |
|---|---|---|
| **CEO / Business leader** | Revenue, strategic fit, speed to value | Part 2 names **Strategic vision & business value**; total indicative € at stake; reactive → proactive. |
| **CTO / Technologist** | Real engineering, not a mock | 132 tests, deterministic-vs-LLM split, grounded Gemini 2.5 Flash + Google Search, WIF; "LLM never moves a number." |
| **Solution architect** | Robust, secure, scalable, compliant | Part 6 names **Solution architecture, scalability, secure & compliant deployment**; Cloud Run + WIF + RBAC + audit; no stored keys. |
| **Product owner** | Adoption, UX, user need | Part 8 names **User experience & adoption**; RM-first, "3 clicks to score", trust on day one. |
| **Control reviewer / Compliance** | Governance, auditability, regulatory safety | Parts 5 & 7 name **Transparency/explainability** and **Responsible & ethical AI**; PO-proposes / Admin-activates / audit trail; human-in-the-loop. |
| **Engineer** | Correctness, honesty | Missing-data caps, corroboration, guardrails, honest provenance ("live vs seed"), graceful fallback. |
| **Startup owner (the client)** | Fairness, no creepy fabrication | "No fabricated data", real companies with citations, private fields left honestly absent, human approval. |

**Delivery techniques baked in:** a provocative one-line hook; problem → turn → proof; a live demo of *real* companies in the first half (show, don't tell); each section names its criterion aloud; a two-voice hand-off mid-Decathlon for pace variety; concrete facts over adjectives; a slow, memorable close ("grounded, explainable, governed, live").

---

## APPENDIX — anticipated Judge Q&A

- **"Is the data real or synthetic?"** The companies are **real** — Airwallex, Payhawk, Modulr, Pleo, Swan and others — discovered with Gemini 2.5 Flash + Google Search grounding, each fact carrying a real citation. Private, unknowable fields are left honestly absent rather than invented. Euro values are labelled **indicative**. If grounding is briefly unavailable we degrade gracefully to clearly-marked seed data and say so.
- **"How do you control hallucination?"** Three-way separation: **facts** are grounded and cited; **decisions** are a deterministic weighted score the LLM cannot alter; **prose** is the only thing the LLM writes — and a guardrail strips banned/over-claim language before any human sees it. Missing data caps the band.
- **"Security and compliance?"** Role-based access across **4 roles**, **Workload Identity Federation** (no stored service-account keys), full audit trail on every action, and governed scoring changes (PO proposes, Admin activates). No confidential client data in the prototype. Deployed on **Google Cloud Run**.
- **"Does it scale across Europe?"** One engine, sector- and corridor-agnostic; Cloud Run scales to zero and out on demand; discovery self-heals across candidate models/regions. Adding a new market is data, not code.
- **"Bias mitigation?"** The score is deterministic and fully explainable — every factor's weight and evidence is visible and inspectable, so bias is auditable rather than hidden in a black box. Weights are governed and change-controlled, and a human approves every recommendation.
- **"What's built vs roadmap?"** **Built & live:** discovery, Decathlon twin, deterministic scoring, guardrails, RBAC, audit, indicative valuation, 132 tests, Cloud Run deployment. **Roadmap:** more opportunity types, an outcome learning loop to tune weights, CRM/core-banking connectors, deeper observability.
- **"How does the 10-dimension Decathlon tie to the theme?"** The event is "The Decathlon" — ten events. Our digital twin scores **ten business dimensions** of maturity: form and substance aligned, not a gimmick — each dimension carries evidence and an indicative value.
- **"Regulatory-advice risk?"** LaunchPad is **decision support, never autonomous**. It surfaces grounded evidence and an explainable score; a qualified human makes and owns every client-facing decision, and that approval is audit-logged. We never issue regulated advice on the model's own authority.
