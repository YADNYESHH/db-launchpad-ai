# LaunchPad AI — Review Against Hackathon Evaluation Criteria

Honest, current-state review against the bank's stated hackathon evaluation criteria (business
impact, responsible/ethical AI, architecture quality, scalability, governance, innovation, UX,
adoption likelihood, trust). Written directly against the live codebase, not aspirationally.

Note on terminology: **"hackathon evaluation criteria"** refers to the judging rubric below.
**"Decathlon"** is a separate, unrelated thing — the product's own name for its 10-dimension
digital-twin scoring model (`scoring/decathlon.py`). Don't conflate the two.

---

## 1. Business impact & alignment with a bank's AI vision

Real alignment on framing: proactive relationship banking instead of reactive product-selling is
well-evidenced (cited EU Commission, EY, and McKinsey research in the original concept document),
and this build added a genuine step toward *tangible* value — an indicative EUR pipeline-value
estimate per startup and a portfolio total, not just a bare 0–100 score. The honest limit: only 1
of the ~9 identified opportunity types (cross-border payments) is actually scored, and the EUR
figures are explicitly labeled "indicative, not validated" — directionally strong, not yet proven
against real outcomes.

## 2. Responsible & ethical AI — fairness, transparency, quality, regulatory compliance

Transparency is the strongest area: every score carries rationale, confidence, and evidence;
missing data is never silently scored as zero; every profile is flagged synthetic or live; live-
discovered facts carry source citations. Regulatory framing is compliant-by-design (explicit
"decision support, not advice," mandatory human approval before anything client-facing).
**Fairness is the real unaddressed gap** — there is no bias assessment of the scoring weights, and
more importantly none of the discovery mechanism itself: a search-grounded discovery agent will
structurally favor startups with a strong English-language web presence. That is a real, nameable
risk that has not been tested or mitigated. Quality: 132+ automated tests and a ruff-clean
codebase, but individual driver formulas are heuristic and documented as assumptions needing
calibration against real RM feedback, which has not happened yet.

## 3. Effective tool use / architecture quality for banking

Coherent, not over-engineered: Firestore + Cloud Run (serverless, scales with usage) + Vertex
Gemini reused consistently for both narrative polish and grounded discovery — the same tool,
the same trust boundary, applied twice rather than two separate risky integrations. Deterministic
scoring is cleanly isolated from the one or two LLM touch-points. Live-debugged three real
production bugs during this build's own deploys (Firestore nested-array rejection, a missing
composite index, a gcloud argument-escaping bug), all fixed and covered by tests — unusually
rigorous for a hackathon build. Not yet bank-grade: no enterprise SSO/Active Directory
integration, and a single shared JWT secret rather than per-user federated identity.

## 4. Realistic scale / adoption across European operations

Technically the stack scales fine. The real blocker to "across European operations" is unchanged
from earlier reviews: no CRM or core-banking integration, no multi-tenant/coverage-team model,
English-only UI and discovery prompts (a genuine gap for pan-European use), and the
single-opportunity-type scope. The architecture does not preclude scaling — nothing here is
throwaway code — but scale is structurally possible, not demonstrated.

## 5. Secure, compliant, responsible deployment — governance, data protection, auditability

Auditability is strong and tested: 100% event coverage across scoring, recommendation, approval,
discovery, and weight changes, with actor and timestamp on every entry. Governance has a real
segregation-of-duties pattern — a Product Owner proposes weight changes, an Admin activates them,
never the same role. Data protection: CORS is restricted to explicit origins, secrets live in
Secret Manager (fixed this build from a worse per-deploy-random-secret state). No data-residency
or DPIA review exists yet for the live discovery calls to Google's Search grounding — low risk
today since only public company names and sectors are sent, but a real review would be needed
before any client data flows through it.

## 6. Innovation & technical excellence

The most defensible innovation claim is architectural, not "flashy AI": deterministic scoring plus
one narrow, guarded LLM touch-point for prose plus a mandatory human-approval gate is a genuine,
thoughtful counter to the common failure mode of wrapping a chatbot and calling it banking AI.
That is a real, differentiated position for a regulated context, backed by unusually rigorous
engineering discipline for a hackathon (automated tests, CI lint/dependency/secret scanning, three
real bugs found and fixed live). It is *not* advanced in the sense of sophisticated multi-agent
reasoning — there is exactly one live-grounded LLM call and one narrative-polish LLM call in the
whole system. Judged against "solid, correct, governed engineering" it clears the bar well; judged
against "sophisticated agentic AI" it does not, and that should be stated plainly rather than
oversold to a technically literate judge.

## 7. Ethical design — bias mitigation, transparency of output

Same split as §2: transparency of output is the standout feature across every review of this
build. Bias mitigation is the one gap that is genuinely unaddressed, not merely incomplete — worth
naming honestly if a judge asks directly, rather than hoping it does not come up.

## 8. User-friendliness / user-centered design

Meaningfully improved through this build: branded chrome, stat tiles, a decision-band legend, an
executive summary strip, a compare view, and a one-click live-portfolio population flow. Still
unvalidated: no accessibility pass, no mobile check, and no real RM has used it yet. Call it
"much improved, self-assessed," not "user-tested."

## 9. Adoption likelihood / operational improvement

Plausible and fairly high-confidence for the one workflow that is fully implemented — the RM
brief format (why-now, evidence, suggested questions, product themes) is exactly the kind of prep
material an RM would want, and nothing in it requires trusting a black box. Lower and unvalidated
confidence for "discover clients we did not know about" — that is the newest work in this build
and has not been used by a real RM yet.

## 10. Trust & confidence via transparent, responsible interaction

This is the strongest-scoring dimension across every review of this build, consistently.
Confidence bands, missing-data flags that block false precision, mandatory approval, a full audit
trail, explicit non-claims, and synthetic/live labeling everywhere — if judges specifically probe
"does this feel like AI a bank could actually trust," this is where the app is strongest, arguably
stronger than its raw technical-cleverness score.

---

## One recommendation

Name the fairness/bias gap (§2/§7) in the pitch, framed as a known limitation and an explicit next
step. Naming your own gap first is more credible to a judge than having them find it.
