# LaunchPad AI — Demo Script & Pitch (2026 TDI Global Hackathon)

**Team:** toruk-makto · **App:** LaunchPad AI — cross-border-payments opportunity intelligence for relationship managers.

---

## 1. The one-line pitch

> **LaunchPad AI turns a bank's relationship managers into proactive advisors: it discovers high-growth startups expanding across borders, scores the *opportunity* with an explainable, human-governed AI pipeline, and quantifies the indicative revenue — before a competitor calls the client first.**

## 2. The problem (30 sec)

Banks sit on rich signals but react late. By the time an RM hears a scale-up is opening in three new countries, a fintech has already won the FX and treasury mandate. RMs are drowning in noise, can't triage, and can't defensibly explain *why* one prospect matters more than another.

## 3. What we built (30 sec)

An agentic decision-support system — **not** an autonomous trader. Every recommendation is:
- **Grounded** — startups are discovered live via Gemini + Google Search grounding, with source citations.
- **Explainable** — a 7-factor weighted opportunity score with per-driver rationale and a 10-dimension "Decathlon" business twin.
- **Quantified** — an indicative annual bank-revenue estimate per opportunity and across the portfolio.
- **Human-governed** — no claim ships without a reviewer; scoring weights are proposed by Product Owners and activated by Admins; every step is audit-logged.

## 4. Live demo flow (3–5 min)

> Log in: `anna.schmidt@launchpad.demo` / `demo1234` (Relationship Manager).

1. **Dashboard first impression (20s).** Navy branded header, governance policy chips ("Human-in-the-loop", "Explainable scoring", "No fabricated data", "Audit-logged", "Grounded discovery"), and stat tiles: **portfolio pipeline value ≈ €212,800**, high-priority count, assessed 6/6.

2. **Ranked portfolio (30s).** Six startups ranked by opportunity score across all four decision bands (High priority → No immediate action). Search + band-filter chips. Point at the decision-band legend: bands map to *actions*, not vanity scores.

3. **Open the top opportunity — PayFlux (score 86) (60s).**
   - **Overview & evidence** — profile, payments, pain points, and signal evidence with sources.
   - **Twin & value tab — the wow moment:**
     - *Agent pipeline* narration shows each agent honestly: Discovery → Digital-twin builder → Decathlon → Scoring → Pipeline valuation → Recommendation+guardrail → Human approval + audit. Seed rows say "Seed data"; live rows say "Live-grounded · N sources" — **we never fake provenance.**
     - *Decathlon grid* — 10 business-maturity dimensions with top drivers.
     - *Indicative pipeline value* — the euro figure with a transparent breakdown (FX fees, cash-management fees, deposit NII) and its stated basis.
   - **Scorecard** — the 7 sub-scores, weights, and per-driver rationale. Show a *missing-data* flag capping the band — honesty by construction.
   - **RM brief** — generate the recommendation. Show the **guardrail** stripping banned/over-claiming language and the single-source **caveats** carried from corroboration.

4. **Live discovery (45s).** Switch to **Live discovery** → sector "cross-border B2B payments" → Discover. New grounded startups appear with citations and are scored on the spot (graceful fallback message if the live call is unavailable — no crash, no fabrication).

5. **Governance (45s).** Switch to **Weights governance**: a Product Owner proposes a new scoring config with a reason; an Admin activates it. Every change is audit-logged. Then **Compare**: put PayFlux, NovaTrade and VerdeGrid side by side — score, band, revenue, pipeline value, top Decathlon dimensions.

6. **Close (15s).** "Grounded, explainable, quantified, and human-governed — from signal to a defensible RM action, with an audit trail behind every number."

## 5. Why this wins (judge framing)

| Judge lens | Our answer |
|---|---|
| **Business value** | Quantified pipeline value (€ per opportunity + portfolio total); RMs act earlier on the *right* targets. |
| **Technical depth** | Multi-agent pipeline, grounded live discovery, deterministic explainable scoring, corroboration + semantic guardrails. |
| **Responsible AI** | Human-in-the-loop, no fabricated data, source citations, banned-claim guardrail, full audit trail, governed weight changes. |
| **Demo polish** | Branded dashboard, ranked portfolio, live search, compare view, governance screen — end-to-end and resilient. |

## 6. Roadmap (if asked)

More opportunity types beyond expansion; a learning loop from RM outcomes; vector search over signals; rate limiting + observability; migration off the deprecated Vertex SDK.

---

### Appendix — demo accounts
| Role | Email | Password |
|---|---|---|
| Relationship Manager | anna.schmidt@launchpad.demo | demo1234 |
| Product Owner | priya.nair@launchpad.demo | demo1234 |
| Control Reviewer | wei.chen@launchpad.demo | demo1234 |
| Admin | admin@launchpad.demo | demo1234 |

### Appendix — resilience notes
- Live discovery **degrades gracefully**: if the grounded call is unavailable, the UI shows an honest "unavailable" banner and the seeded portfolio remains fully functional.
- All scoring is **deterministic** and unit-tested (113 backend tests), so the demo behaves identically every run.
