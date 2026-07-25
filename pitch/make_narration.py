"""Generate the two-voice pitch narration audio using macOS `say`.

ARIA (first half) → voice "Samantha" (en_US female).
ETHAN (second half) → voice "Daniel" (en_GB male).

Text is derived from pitch/narration-script.md, cleaned for text-to-speech
(acronyms spelled with periods so they read as letters, `[[slnc N]]` inline
pauses for natural beats). Produces pitch/recordings/narration.m4a.

Run:  python3 pitch/make_narration.py
Needs: macOS `say`; ffmpeg is taken from the imageio-ffmpeg wheel if present,
else from PATH.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REC = Path(__file__).parent / "recordings"
REC.mkdir(parents=True, exist_ok=True)

RATE = "190"  # words-per-minute; brisk-but-warm so the full pitch lands under 5:00
ARIA_VOICE = os.getenv("ARIA_VOICE", "Karen")    # female narrator (first half)
ETHAN_VOICE = os.getenv("ETHAN_VOICE", "Daniel")  # male narrator (second half)

# --- ARIA (Samantha) — parts 1–4 -------------------------------------------
ARIA_TEXT = """
What if a relationship manager could call the right company, at exactly the right moment, with a reason they can prove — before a competitor even notices? [[slnc 450]]
Today, banking is reactive. A scale-up opens new countries, hires abroad, raises a round — and that signal is public for days before the bank acts. Relationship managers drown in hundreds of names, with no way to triage, and no defensible reason why one matters more than another. [[slnc 300]]
The timing is everything — and today, the bank misses it. So we built D.B. LaunchPad A.I. — and it is live, on Google Cloud, right now. [[slnc 600]]
This is our first criterion — strategic vision and business value — and I will start where a leader starts: the money. [[slnc 400]]
Here is the executive portfolio view. Across it, LaunchPad quantifies the total indicative euro value at stake — the annual revenue this pipeline represents in F.X., cash-management fees, and deposit income. Companies are ranked by opportunity — green for act-now, down to grey for hold. [[slnc 300]]
In one glance, the bank moves from reactive to proactive — a strategic shortlist, priced, in front of the right relationship manager. [[slnc 600]]
And this is not a mock-up. These are real companies — Airwallex, Payhawk, Modulr, Pleo, Swan, Juni, and TransferMate. [[slnc 350]]
Every profile is built by grounded discovery — Gemini 2.5 Flash, with Google Search grounding — so each fact carries a real citation you can click through to its source. Where a company is private and a field is genuinely unknown, we leave it honestly absent. [[slnc 300]]
That is the rule the whole system obeys: no fabricated data. The value you just saw is built on evidence a bank can defend. [[slnc 600]]
Now open the top opportunity — and here is our Decathlon digital twin, the heart of our innovation and technical excellence. [[slnc 350]]
Ten business dimensions of maturity — a tribute to the ten-event Decathlon — each with an indicative euro value and a transparent breakdown. The agent pipeline even tells you, honestly, whether this came from live grounded search or seed data. [[slnc 300]]
Ten dimensions, one defensible twin. My colleague Ethan will now show you why a bank can trust the number behind it. [[slnc 500]]
"""

# --- ETHAN (Daniel) — parts 5–9 --------------------------------------------
ETHAN_TEXT = """
Thank you, Aria. This is our next criterion — transparency and explainability: responsible A.I. by design. [[slnc 400]]
The score is deterministic — a transparent, weighted model, reproducible on every run. Each factor shows its weight, its evidence, and its rationale. Nothing is hidden. A guardrail strips any over-claim before a human ever sees it; and where data is missing, the priority band is capped — honesty, enforced in code. [[slnc 300]]
The language model only phrases the prose. It never moves a number. That separation is what makes the score explainable — and trustworthy. [[slnc 600]]
Next: solution architecture, scalability, and secure, compliant deployment — proven through governance. [[slnc 350]]
Watch the roles. A Product Owner proposes new scoring weights. An Admin activates them. And every change lands in an immutable audit trail — proposer, approver, timestamp. Four distinct roles, enforced by role-based access control. [[slnc 300]]
It runs on Google Cloud Run — scaling to zero, scaling out on demand. There are no stored service-account keys; we authenticate with Workload Identity Federation. And it is backed by 132 automated tests in continuous integration. [[slnc 300]]
Governed changes, least-privilege access, a full audit — architecture a regulator can inspect. [[slnc 600]]
For a bank, trust is the product — so this criterion, responsible and ethical A.I., is architected in, not bolted on. [[slnc 350]]
Provenance on every fact, with citations. Guardrails that block over-claims. Human-in-the-loop approval on every single recommendation — the A.I. advises; a person decides. And because scores are explainable and every action is audited, the whole system is fair, transparent, auditable, and regulatory-safe. [[slnc 300]]
We never give regulated advice autonomously. A human owns the outcome — always. [[slnc 600]]
None of this matters if a relationship manager will not use it — so our final criterion is user experience and adoption. [[slnc 350]]
It is relationship-manager-first: from portfolio, to a scored, evidence-backed brief, in three clicks. No dashboards to configure, no jargon — just a ranked shortlist, and a reason to call. [[slnc 300]]
And when the relationship manager has a follow-up — who are their competitors? — they simply ask. Our grounded, guardrailed, audit-logged chat answers only from real evidence — never a guess. [[slnc 300]]
And because every claim is grounded, and every score explained, the relationship manager trusts it on day one. That is how adoption really happens — trust, not training. [[slnc 500]]
Everything you saw is built, tested, and live today. Next: more opportunity types, an outcome loop that tunes the weights, and C.R.M. connectors. [[slnc 350]]
D.B. LaunchPad A.I. — grounded, explainable, governed, and live. From a public signal, to a defensible action — with an audit trail behind every number. [[slnc 700]]
Thank you. [[slnc 300]]
"""


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _say(voice: str, text: str, out_aiff: Path) -> None:
    txt = REC / f"_{out_aiff.stem}.txt"
    text = text.strip().replace("[[slnc 700]]", "[[slnc 480]]").replace("[[slnc 600]]", "[[slnc 430]]")
    txt.write_text(text, encoding="utf-8")
    subprocess.run(
        ["say", "-v", voice, "-r", RATE, "-f", str(txt), "-o", str(out_aiff)],
        check=True,
    )


def main() -> None:
    aria = REC / "aria.aiff"
    ethan = REC / "ethan.aiff"
    print(f"Synthesising ARIA ({ARIA_VOICE})…")
    _say(ARIA_VOICE, ARIA_TEXT, aria)
    print(f"Synthesising ETHAN ({ETHAN_VOICE})…")
    _say(ETHAN_VOICE, ETHAN_TEXT, ethan)

    out = REC / "narration.m4a"
    print("Merging voices → narration.m4a …")
    subprocess.run(
        [
            _ffmpeg(), "-y", "-loglevel", "error",
            "-i", str(aria), "-i", str(ethan),
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[a]",
            "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(out),
        ],
        check=True,
    )

    # report duration
    ff = _ffmpeg()
    probe = subprocess.run([ff, "-i", str(out)], capture_output=True, text=True)
    for line in probe.stderr.splitlines():
        if "Duration" in line:
            print(line.strip())
    print(f"\n✅ Narration audio: {out}")


if __name__ == "__main__":
    sys.exit(main())
