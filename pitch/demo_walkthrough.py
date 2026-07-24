"""DB LaunchPad AI — automated demo walkthrough for screen-recording the pitch.

This drives a real browser through the app, screen by screen, pausing on each
view with a caption overlay so you can read the matching narration (see
``pitch/narration-script.md``). Record your screen while this runs.

SETUP (one time):
    pip install playwright
    playwright install chromium

RUN against the LOCAL app (recommended for a smooth, offline-safe demo):
    # start the backend first, serving the built frontend:
    #   cd app && source .venv/bin/activate && uvicorn backend.main:app --port 8099
    python pitch/demo_walkthrough.py

RUN against the LIVE Cloud Run service:
    DEMO_URL=https://launchpad-ai-156042242219.europe-west1.run.app python pitch/demo_walkthrough.py

The walkthrough logs in as MULTIPLE roles (RM → Product Owner → Admin) to
demo the governance features, prominently shows LIVE real companies, and adds
on-screen captions mapping each screen to the 4 hackathon assessment criteria.

OPTIONS (env vars):
    DEMO_URL           base URL (default http://localhost:8099)
    DEMO_PASS          login password (default demo1234)
    DEMO_SPEED         pacing multiplier, 1.0 = normal, 1.5 = slower (default 1.2)
    DEMO_RM_LABEL      combobox label for the RM demo user (default "Anna Schmidt")
    DEMO_PO_LABEL      combobox label for the Product Owner (default "Priya Nair")
    DEMO_REVIEWER_LABEL combobox label for the Control Reviewer (default "Wei Chen")
    DEMO_ADMIN_LABEL   combobox label for the Admin (default "Admin")

The script is defensive: if a screen element is not found it logs and moves on,
so a small UI change never aborts the recording.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

BASE = os.getenv("DEMO_URL", "http://localhost:8099").rstrip("/")
EMAIL = os.getenv("DEMO_EMAIL", "anna.schmidt@launchpad.demo")
EMAIL_LABEL = os.getenv("DEMO_EMAIL_LABEL", "")  # e.g. "Priya Nair (Product Owner)"; empty = keep default
PASSWORD = os.getenv("DEMO_PASS", "demo1234")
SPEED = float(os.getenv("DEMO_SPEED", "1.2"))
DO_LIVE = os.getenv("DEMO_LIVE", "0") in ("1", "true", "True", "yes")
HEADLESS = os.getenv("DEMO_HEADLESS", "0") in ("1", "true", "True", "yes")
REC_DIR = Path(os.getenv("DEMO_REC_DIR", str(Path(__file__).parent / "recordings")))


def beat(seconds: float) -> None:
    """Pause, scaled by DEMO_SPEED, so narration can keep up."""
    time.sleep(seconds * SPEED)


def caption(page: Page, title: str, subtitle: str = "") -> None:
    """Show a branded caption overlay in the corner of the page. Never raises."""
    if page.is_closed():
        return
    try:
        page.evaluate(
        """([title, subtitle]) => {
            let el = document.getElementById('demo-caption');
            if (!el) {
                el = document.createElement('div');
                el.id = 'demo-caption';
                el.style.cssText = [
                    'position:fixed','left:24px','bottom:24px','z-index:99999',
                    'max-width:520px','padding:14px 18px','border-radius:12px',
                    'font-family:-apple-system,Segoe UI,Roboto,sans-serif',
                    'color:#fff','background:linear-gradient(135deg,#0a1f5c,#1a52d6)',
                    'box-shadow:0 12px 30px rgba(10,31,68,.45)',
                    'border:1px solid rgba(255,255,255,.18)',
                    'transition:opacity .3s ease','opacity:0'
                ].join(';');
                document.body.appendChild(el);
            }
            el.innerHTML =
                '<div style="font-weight:800;font-size:16px;letter-spacing:.2px">' + title + '</div>' +
                (subtitle ? '<div style="font-size:13px;color:#cfe0ff;margin-top:4px">' + subtitle + '</div>' : '');
            requestAnimationFrame(() => { el.style.opacity = '1'; });
        }""",
            [title, subtitle],
        )
    except Exception as exc:  # noqa: BLE001 - captions must never break the demo
        print(f"  [caption skipped] {title}: {type(exc).__name__}")


def safe(fn, label: str) -> bool:
    """Run a step, swallowing errors so the recording never aborts."""
    try:
        fn()
        return True
    except PWTimeout:
        print(f"  [skip] timeout on: {label}")
    except Exception as exc:  # noqa: BLE001 - demo resilience
        print(f"  [skip] {label}: {type(exc).__name__}: {exc}")
    return False


def click_text(page: Page, text: str, timeout: int = 6000) -> None:
    page.get_by_text(text, exact=False).first.click(timeout=timeout)


def click_role(page: Page, role: str, name: str, timeout: int = 6000) -> None:
    page.get_by_role(role, name=name).first.click(timeout=timeout)


# Real, live companies currently in the deployed portfolio.
LIVE_COMPANIES = [
    "Airwallex", "Payhawk", "Modulr", "Pleo", "Swan", "Juni",
    "TransferMate", "Ankorstore", "ManoMano", "Everstox", "InstaFreight",
]


def login(page: Page, email_label: str) -> None:
    """Sign in on the login page as the demo user with the given visible label.

    Selects the option whose visible text is ``email_label`` in the role/email
    combobox, fills the prefilled password with 'demo1234', and clicks "Sign in".
    Wrapped in safe() by callers so a missing element never aborts the recording.
    """
    def do_login():
        page.get_by_role("combobox").first.select_option(label=email_label)
        pw = page.get_by_role("textbox", name="Password")
        pw.fill(PASSWORD)
        click_role(page, "button", "Sign in")
    safe(do_login, f"login as {email_label}")
    page.wait_for_load_state("networkidle")


def sign_out(page: Page) -> None:
    """Click 'Sign out' and wait for the login page. Defensive."""
    safe(lambda: click_role(page, "button", "Sign out"), "sign out")
    page.wait_for_load_state("networkidle")
    beat(1.5)


# Visible combobox labels for each demo role (adjust here if the UI labels change).
RM_LABEL = os.getenv("DEMO_RM_LABEL", "Anna Schmidt")
PO_LABEL = os.getenv("DEMO_PO_LABEL", "Priya Nair")
REVIEWER_LABEL = os.getenv("DEMO_REVIEWER_LABEL", "Wei Chen")
ADMIN_LABEL = os.getenv("DEMO_ADMIN_LABEL", "Admin")


def run(page: Page) -> None:
    # ---- 0. Open ----
    print("Opening", BASE)
    page.goto(BASE, wait_until="networkidle")
    beat(1.5)

    # ---- 1. Login as Relationship Manager ----
    caption(page, "DB LaunchPad AI",
            "Live, governed opportunity intelligence")
    safe(lambda: login(page, RM_LABEL), "login as RM")
    beat(2.5)

    # ---- 2. Executive view — strategy & value ----
    caption(page, "Portfolio value & strategy",
            "Assessment: Strategic vision & business value")
    safe(lambda: click_role(page, "button", "Executive"), "executive view")
    page.wait_for_load_state("networkidle")
    beat(7.0)  # KPIs, pipeline value, band distribution, top opportunities

    # ---- 3. Portfolio — real, live companies only ----
    caption(page, "Real companies, discovered live",
            "Assessment: No fabricated data")
    safe(lambda: click_role(page, "button", "Portfolio"), "portfolio view")
    page.wait_for_load_state("networkidle")
    beat(2.0)
    # Filter to LIVE-sourced companies if the source filter is present.
    safe(lambda: click_role(page, "button", "Live"), "live source filter")
    beat(3.0)

    # Open a LIVE company by searching its name.
    company = LIVE_COMPANIES[0]  # Airwallex
    def open_live_company():
        box = page.get_by_role("textbox").first
        box.fill(company)
        beat(1.5)
        page.locator("ul.portfolio-list li").first.click(timeout=6000)
    safe(open_live_company, f"open live company {company}")
    page.wait_for_load_state("networkidle")
    caption(page, f"Live company · {company}",
            "Assessment: No fabricated data")
    beat(3.5)

    # ---- 4. Twin & value tab ----
    caption(page, "Decathlon digital twin + € value",
            "Assessment: Innovation & technical excellence")
    safe(lambda: click_role(page, "button", "Twin & value"), "twin tab")
    beat(3.0)
    # Show the live-discovery provenance / citations.
    safe(lambda: page.mouse.wheel(0, 600), "scroll for provenance")
    beat(4.0)

    # ---- 5. Scorecard — explainable, deterministic ----
    caption(page, "Explainable, deterministic scoring",
            "Assessment: Transparency & explainability")
    safe(lambda: click_role(page, "button", "Score now"), "score now")
    beat(2.5)
    safe(lambda: click_role(page, "button", "Re-score"), "re-score (already scored)")
    beat(1.0)
    safe(lambda: click_role(page, "button", "Scorecard"), "scorecard tab")
    beat(5.0)

    # ---- 5b. RM asks a grounded, guardrailed question ----
    caption(page, "Ask the RM chat — grounded, guardrailed, audited",
            "Assessment: Responsible AI · UX & adoption")
    safe(lambda: click_role(page, "button", "Ask a question"), "ask tab")
    beat(1.5)
    def ask_question():
        box = page.get_by_placeholder("Ask a question about this startup", exact=False)
        box.fill("Who are this company's main competitors?")
        page.get_by_role("button", name="Ask").first.click()
    safe(ask_question, "ask a question")
    beat(9.0)  # allow the grounded answer to arrive

    # ---- 6. Product Owner proposes a weight change ----
    sign_out(page)
    caption(page, "Governed model weights — Product Owner proposes",
            "Assessment: Solution architecture & governance")
    safe(lambda: login(page, PO_LABEL), "login as Product Owner")
    beat(2.0)
    safe(lambda: click_role(page, "button", "Weights governance"), "weights view (PO)")
    page.wait_for_load_state("networkidle")
    beat(3.0)
    safe(lambda: page.get_by_role("textbox").last.fill(
        "Increase early-signal weight after RM feedback"), "change reason")
    beat(2.0)
    safe(lambda: click_role(page, "button", "Propose"), "propose weight change")
    beat(3.0)

    # ---- 7. Admin activates — audit-logged ----
    sign_out(page)
    caption(page, "Admin activates — every change audit-logged",
            "Assessment: Secure, compliant deployment")
    safe(lambda: login(page, ADMIN_LABEL), "login as Admin")
    beat(2.0)
    safe(lambda: click_role(page, "button", "Weights governance"), "weights view (Admin)")
    page.wait_for_load_state("networkidle")
    beat(2.5)
    safe(lambda: click_role(page, "button", "Activate"), "activate weight change")
    beat(3.5)

    # ---- 8. Responsible AI ----
    caption(page, "Responsible AI: provenance, guardrails, audit",
            "Assessment: Responsible & ethical AI")
    safe(lambda: click_role(page, "button", "Responsible AI"), "responsible ai view")
    page.wait_for_load_state("networkidle")
    beat(7.0)

    # ---- 9. Compare — side-by-side decision support ----
    caption(page, "Side-by-side decision support",
            "Assessment: User experience & adoption")
    safe(lambda: click_role(page, "button", "Compare"), "compare view")
    page.wait_for_load_state("networkidle")
    beat(5.0)

    # ---- 10. Close ----
    caption(page, "Grounded · Explainable · Governed · Live",
            "DB LaunchPad AI")
    beat(5.0)
    print("Demo walkthrough complete.")


def main() -> None:
    REC_DIR.mkdir(parents=True, exist_ok=True)
    size = {"width": 1512, "height": 944}
    launch_args = ["--start-fullscreen", "--no-first-run", "--disable-session-crashed-bubble",
                   "--disable-infobars", "--hide-crash-restore-bubble"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, args=launch_args)
        context = browser.new_context(
            viewport=size,
            record_video_dir=str(REC_DIR),
            record_video_size=size,
        )
        page = context.new_page()
        video = page.video
        try:
            run(page)
        except Exception as exc:  # noqa: BLE001 - always finish and save the video
            print(f"Run interrupted ({type(exc).__name__}: {exc}); saving partial video.")
        finally:
            try:
                context.close()  # finalises the video file
            except Exception:  # noqa: BLE001
                pass
            try:
                browser.close()
            except Exception:  # noqa: BLE001
                pass
        if video is not None:
            try:
                src = Path(video.path())
                dest = REC_DIR / "db-launchpad-ai-demo.webm"
                if src.exists():
                    src.replace(dest)
                    print(f"\n✅ Demo video saved: {dest}")
                    print("   Convert to mp4 if needed: ffmpeg -i "
                          f"'{dest}' pitch/recordings/db-launchpad-ai-demo.mp4")
            except Exception as exc:  # noqa: BLE001
                print(f"Video saved in {REC_DIR} (path lookup failed: {exc})")


if __name__ == "__main__":
    main()
