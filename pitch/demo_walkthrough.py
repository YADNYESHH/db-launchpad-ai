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

OPTIONS (env vars):
    DEMO_URL     base URL (default http://localhost:8099)
    DEMO_EMAIL   login email (default anna.schmidt@launchpad.demo)
    DEMO_PASS    login password (default demo1234)
    DEMO_SPEED   pacing multiplier, 1.0 = normal, 1.5 = slower for narration (default 1.2)
    DEMO_LIVE    "1" to click "Populate live portfolio" (needs cloud creds; default "0")

The script is defensive: if a screen element is not found it logs and moves on,
so a small UI change never aborts the recording.
"""

from __future__ import annotations

import os
import time

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

BASE = os.getenv("DEMO_URL", "http://localhost:8099").rstrip("/")
EMAIL = os.getenv("DEMO_EMAIL", "anna.schmidt@launchpad.demo")
EMAIL_LABEL = os.getenv("DEMO_EMAIL_LABEL", "")  # e.g. "Priya Nair (Product Owner)"; empty = keep default
PASSWORD = os.getenv("DEMO_PASS", "demo1234")
SPEED = float(os.getenv("DEMO_SPEED", "1.2"))
DO_LIVE = os.getenv("DEMO_LIVE", "0") in ("1", "true", "True", "yes")


def beat(seconds: float) -> None:
    """Pause, scaled by DEMO_SPEED, so narration can keep up."""
    time.sleep(seconds * SPEED)


def caption(page: Page, title: str, subtitle: str = "") -> None:
    """Show a branded caption overlay in the corner of the page."""
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


def run(page: Page) -> None:
    # ---- 0. Open ----
    print("Opening", BASE)
    page.goto(BASE, wait_until="networkidle")
    beat(1.5)

    # ---- 1. Login ----
    caption(page, "DB LaunchPad AI", "Signing in as a Relationship Manager")
    def do_login():
        # The email selector defaults to the Relationship Manager demo user.
        # Fill the password and sign in. (Override via DEMO_EMAIL_LABEL if needed.)
        if EMAIL_LABEL:
            try:
                page.get_by_role("combobox").first.select_option(label=EMAIL_LABEL)
            except Exception:
                pass  # default selection is fine
        pw = page.get_by_role("textbox", name="Password")
        pw.fill(PASSWORD)
        click_role(page, "button", "Sign in")
    safe(do_login, "login")
    page.wait_for_load_state("networkidle")
    beat(2.5)

    # ---- 2. Dashboard / governance ----
    caption(page, "Governance, front and centre",
            "Human-in-the-loop · Explainable · No fabricated data · Audit-logged")
    beat(4.0)

    # ---- 3. Ranked portfolio ----
    caption(page, "Portfolio, ranked by opportunity",
            "Total indicative pipeline value at a glance · traffic-light decision bands")
    beat(4.0)

    # ---- 4. Open the top company ----
    caption(page, "Open the top opportunity", "The highest-scoring company in the book")
    safe(lambda: page.locator("ul.portfolio-list li").first.click(timeout=6000), "open top startup")
    page.wait_for_load_state("networkidle")
    beat(2.5)

    # ---- 5. Twin & value tab ----
    caption(page, "Decathlon digital twin + euro value",
            "10 business dimensions · indicative annual bank revenue · honest provenance")
    safe(lambda: click_role(page, "button", "Twin & value"), "twin tab")
    beat(5.0)

    # ---- 6. Scorecard ----
    caption(page, "Explainable scorecard",
            "7 factors · weights · evidence · missing data caps the band")
    safe(lambda: click_role(page, "button", "Scorecard"), "scorecard tab")
    beat(2.0)
    # ensure it is scored
    safe(lambda: click_role(page, "button", "Score now"), "score now")
    beat(4.0)

    # ---- 7. RM brief + guardrail ----
    caption(page, "RM brief — guardrailed",
            "One click · banned claims stripped · a human approves before use")
    safe(lambda: click_role(page, "button", "Generate RM brief"), "generate brief")
    beat(5.0)

    # ---- 8. Audit trail ----
    caption(page, "Full audit trail", "Every step is logged — from score to approval")
    safe(lambda: click_text(page, "Audit trail"), "audit tab")
    beat(4.0)

    # ---- 9. Live discovery ----
    caption(page, "Live, grounded discovery",
            "Real companies via Gemini + Google Search, with source citations")
    safe(lambda: click_role(page, "button", "Live discovery"), "discovery view")
    page.wait_for_load_state("networkidle")
    beat(3.0)
    if DO_LIVE:
        caption(page, "Populating a live portfolio", "Discovering real companies across sectors…")
        safe(lambda: click_role(page, "button", "Populate live portfolio"), "populate live")
        beat(8.0)

    # ---- 10. Compare ----
    caption(page, "Compare opportunities side by side",
            "Score · band · revenue · pipeline value · top Decathlon dimensions")
    safe(lambda: click_role(page, "button", "Compare"), "compare view")
    page.wait_for_load_state("networkidle")
    beat(4.5)

    # ---- 11. Weights governance ----
    caption(page, "Governed scoring weights",
            "Proposed by Product Owners · activated by Admins · fully audited")
    safe(lambda: click_role(page, "button", "Weights governance"), "weights view")
    page.wait_for_load_state("networkidle")
    beat(4.0)

    # ---- 12. Close ----
    caption(page, "Grounded · Explainable · Governed · Live",
            "DB LaunchPad AI — from a public signal to a defensible action")
    beat(5.0)
    print("Demo walkthrough complete.")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            run(page)
        finally:
            beat(2.0)
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
