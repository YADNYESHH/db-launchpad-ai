"""End-to-end UI test suite for DB LaunchPad AI.

Drives the real, served frontend (FastAPI serves frontend/dist) with Playwright
and exercises every clickable control across all four roles. Each test runs in a
fresh browser context for isolation.

Run against a locally served build:
    cd app && source .venv/bin/activate \
      && STORE_BACKEND=memory uvicorn backend.main:app --port 8099   # (in one shell)
    E2E_URL=http://localhost:8099 python e2e/run_ui_tests.py         # (in another)

Exit code = number of failing test cases (0 == all green).
"""

from __future__ import annotations

import os
import sys
import traceback
from typing import Callable

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

BASE = os.getenv("E2E_URL", "http://localhost:8099").rstrip("/")
PASSWORD = "demo1234"
HEADLESS = os.getenv("E2E_HEADLESS", "1") != "0"

ROLE_LABELS = {
    "rm": "Anna Schmidt (Relationship Manager)",
    "po": "Priya Nair (Product Owner)",
    "cr": "Wei Chen (Control Reviewer)",
    "admin": "Admin User (Admin)",
}

NAV_LABELS = {
    "portfolio": "Portfolio",
    "executive": "Executive",
    "discovery": "Live discovery",
    "compare": "Compare",
    "weights": "Weights governance",
    "responsible": "Responsible AI",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def goto_login(page: Page) -> None:
    # Clear any persisted auth token so we always land on the login form, even
    # when re-authenticating as a different role within the same context.
    page.goto(BASE, wait_until="domcontentloaded")
    page.evaluate("() => window.localStorage.clear()")
    page.goto(BASE, wait_until="domcontentloaded")
    page.locator(".login-card select").wait_for(state="visible", timeout=20000)


def login(page: Page, role: str, password: str = PASSWORD) -> None:
    goto_login(page)
    page.locator(".login-card select").select_option(label=ROLE_LABELS[role])
    page.locator('input[type="password"]').fill(password)
    page.get_by_role("button", name="Sign in").click()
    page.locator(".view-nav").wait_for(state="visible", timeout=20000)


def goto_view(page: Page, key: str) -> None:
    page.locator(".view-nav-btn", has_text=NAV_LABELS[key]).first.click()


def open_first_company(page: Page) -> None:
    """From the portfolio view, select the top-ranked company."""
    goto_view(page, "portfolio")
    page.locator("ul.portfolio-list li").first.wait_for(state="visible", timeout=20000)
    page.locator("ul.portfolio-list li").first.click()
    page.locator(".startup-detail").wait_for(state="visible", timeout=20000)


def ensure_scored(page: Page) -> None:
    """Click 'Score now' if needed and wait until the Scorecard tab enables.

    Scoring is deterministic but a cold/loaded deployment can take longer, so we
    poll for the enabled state rather than assuming a fixed delay.
    """
    btn = page.locator(".startup-header-actions button").first
    label = (btn.inner_text() or "").strip().lower()
    if label.startswith("score"):  # 'Score now' (not 'Re-score')
        btn.click()
    scorecard = page.locator("nav.tabs button", has_text="Scorecard")
    for _ in range(60):  # up to ~30s
        try:
            if scorecard.is_enabled():
                return
        except PWTimeout:
            pass
        page.wait_for_timeout(500)
    raise AssertionError("Scorecard tab did not enable after scoring")


def click_tab_and_wait_active(page: Page, label: str) -> None:
    """Click a detail tab and wait until it carries the 'active' class."""
    tab = page.locator("nav.tabs button", has_text=label).first
    tab.click()
    for _ in range(20):  # up to ~5s
        if "active" in (tab.get_attribute("class") or ""):
            return
        page.wait_for_timeout(250)
    raise AssertionError(f"tab '{label}' not active after click")


# --------------------------------------------------------------------------- #
# Test cases  (each raises AssertionError / PWTimeout on failure)
# --------------------------------------------------------------------------- #
def t_login_page_renders(page: Page) -> None:
    goto_login(page)
    assert page.locator("h1", has_text="LaunchPad AI").is_visible()
    assert page.get_by_role("button", name="Sign in").is_visible()
    # Default selection is the RM.
    assert page.locator(".login-card select").input_value() == "anna.schmidt@launchpad.demo"


def t_login_wrong_password(page: Page) -> None:
    goto_login(page)
    page.locator('input[type="password"]').fill("wrong-password")
    page.get_by_role("button", name="Sign in").click()
    banner = page.locator(".error-banner")
    banner.wait_for(state="visible", timeout=15000)
    assert "Login failed" in banner.inner_text()


def _login_role(page: Page, role: str) -> None:
    login(page, role)
    assert page.locator(".view-nav").is_visible()


def t_login_rm(page: Page) -> None:
    _login_role(page, "rm")


def t_login_po(page: Page) -> None:
    _login_role(page, "po")


def t_login_cr(page: Page) -> None:
    _login_role(page, "cr")


def t_login_admin(page: Page) -> None:
    _login_role(page, "admin")


def t_logout(page: Page) -> None:
    login(page, "rm")
    page.locator(".lp-signout-btn").click()
    page.locator(".login-card select").wait_for(state="visible", timeout=15000)


def t_nav_all_views(page: Page) -> None:
    login(page, "rm")
    for key, label in NAV_LABELS.items():
        btn = page.locator(".view-nav-btn", has_text=label).first
        btn.click()
        page.wait_for_timeout(150)
        cls = btn.get_attribute("class") or ""
        assert "active" in cls, f"nav '{label}' did not become active"


def t_portfolio_list_renders(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "portfolio")
    page.locator("ul.portfolio-list li").first.wait_for(state="visible", timeout=20000)
    assert page.locator("ul.portfolio-list li").count() >= 1


def t_portfolio_source_filters(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "portfolio")
    page.locator("ul.portfolio-list li").first.wait_for(state="visible", timeout=20000)
    for label in ("All sources", "Live", "Synthetic"):
        chip = page.locator(".pf-source-chip", has_text=label).first
        chip.click()
        page.wait_for_timeout(120)
        assert "active" in (chip.get_attribute("class") or "")


def t_portfolio_band_filters(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "portfolio")
    page.locator("ul.portfolio-list li").first.wait_for(state="visible", timeout=20000)
    for label in ("All", "High priority", "Monitor", "Validate", "No action"):
        chip = page.locator(".portfolio-chip", has_text=label).first
        chip.click()
        page.wait_for_timeout(120)
        assert "active" in (chip.get_attribute("class") or "")


def t_portfolio_search(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "portfolio")
    first = page.locator("ul.portfolio-list li").first
    first.wait_for(state="visible", timeout=20000)
    name = (first.locator(".portfolio-item-title strong").inner_text() or "").strip()
    assert name, "could not read first company name"
    page.locator(".portfolio-search").fill(name)
    page.wait_for_timeout(250)
    assert page.locator("ul.portfolio-list li").count() >= 1
    # A nonsense query yields the empty-state message.
    page.locator(".portfolio-search").fill("zzz-no-such-company-xyz")
    page.wait_for_timeout(250)
    assert page.locator(".portfolio-empty").is_visible()


def t_portfolio_select_company(page: Page) -> None:
    login(page, "rm")
    open_first_company(page)
    assert page.locator(".startup-detail h2").first.is_visible()


def t_detail_score_now(page: Page) -> None:
    login(page, "rm")
    open_first_company(page)
    ensure_scored(page)
    # Scorecard tab should be enabled and a summary strip present.
    scorecard_tab = page.locator("nav.tabs button", has_text="Scorecard")
    assert scorecard_tab.is_enabled()


def t_detail_all_tabs(page: Page) -> None:
    login(page, "rm")
    open_first_company(page)
    ensure_scored(page)
    for label in ("Overview & evidence", "Twin & value", "Scorecard", "Audit trail", "Ask a question"):
        click_tab_and_wait_active(page, label)


def t_detail_generate_brief(page: Page) -> None:
    login(page, "rm")
    open_first_company(page)
    ensure_scored(page)
    # A high-priority company briefs directly; a lower band is a governed case
    # that requires the explicit 'Force draft brief' path. Exercise whichever
    # applies so a real recommendation is produced either way.
    force_btn = page.locator(".startup-header-actions button", has_text="Force draft brief")
    if force_btn.count() >= 1:
        force_btn.first.click()
    else:
        page.locator(".startup-header-actions button", has_text="Generate RM brief").first.click()
    tab = page.locator("nav.tabs button", has_text="RM brief")
    # Poll until the recommendation lands and the tab enables (deterministic
    # template render; no live LLM required).
    for _ in range(50):
        if tab.is_enabled():
            break
        page.wait_for_timeout(500)
    assert tab.is_enabled(), "RM brief tab did not enable after generating a brief"


def t_detail_ask_chat(page: Page) -> None:
    login(page, "rm")
    open_first_company(page)
    page.locator("nav.tabs button", has_text="Ask a question").click()
    page.locator(".chat-input").wait_for(state="visible", timeout=15000)
    page.locator(".chat-input").fill("Who are this company's main competitors?")
    page.locator(".chat-send-btn").click()
    # An assistant reply bubble must appear (grounded-first answer, no crash).
    page.locator(".chat-msg-assistant .chat-bubble").first.wait_for(state="visible", timeout=45000)
    assert page.locator(".error-banner").count() == 0, "chat raised an error banner"


def t_executive_renders(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "executive")
    page.locator(".exec-hero-value").wait_for(state="visible", timeout=20000)
    assert page.locator(".exec-tile").count() >= 4


def t_executive_row_click(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "executive")
    row = page.locator("tr.exec-row").first
    row.wait_for(state="visible", timeout=20000)
    row.click()
    # Clicking an opportunity jumps to the portfolio view with the company open.
    page.locator(".startup-detail").wait_for(state="visible", timeout=20000)


def t_compare_toggle(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "compare")
    boxes = page.locator(".cmp-selector-item input[type=checkbox]")
    boxes.first.wait_for(state="visible", timeout=20000)
    n = boxes.count()
    assert n >= 2, "need at least two companies to compare"
    # Clear any default selection, then select two and confirm the table renders.
    for i in range(n):
        cb = boxes.nth(i)
        if cb.is_checked():
            cb.uncheck()
    boxes.nth(0).check()
    boxes.nth(1).check()
    page.wait_for_timeout(200)
    assert page.locator("table.cmp-table").is_visible()


def t_compare_max_three(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "compare")
    boxes = page.locator(".cmp-selector-item input[type=checkbox]")
    boxes.first.wait_for(state="visible", timeout=20000)
    for i in range(boxes.count()):
        cb = boxes.nth(i)
        if cb.is_checked():
            cb.uncheck()
    to_check = min(4, boxes.count())
    for i in range(to_check):
        cb = boxes.nth(i)
        if not cb.is_disabled():
            cb.check()
    checked = sum(1 for i in range(boxes.count()) if boxes.nth(i).is_checked())
    assert checked <= 3, f"selection exceeded max of 3 (got {checked})"


def t_discovery_controls(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "discovery")
    page.locator(".disc-input").wait_for(state="visible", timeout=20000)
    page.locator(".disc-input").fill("cross-border B2B payments")
    page.locator(".disc-select").select_option("3")
    page.locator(".disc-button").click()
    # Either results, an info banner, or an error banner must appear — never a hang/crash.
    page.locator(".disc-results, .disc-banner").first.wait_for(state="visible", timeout=60000)


def t_discovery_populate_button(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "discovery")
    btn = page.locator("button", has_text="Populate live portfolio")
    btn.wait_for(state="visible", timeout=20000)
    btn.click()
    # A status or error banner must appear (live may be unavailable locally).
    page.locator(".live-populate-status, .error-banner").first.wait_for(state="visible", timeout=60000)


def t_weights_readonly_rm(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "weights")
    page.locator(".wa-panel").wait_for(state="visible", timeout=20000)
    assert page.locator("#wa-change-reason").count() == 0, "RM must not see the propose form"
    assert page.locator(".wa-note").is_visible()


def t_weights_propose_po(page: Page) -> None:
    login(page, "po")
    goto_view(page, "weights")
    page.locator("#wa-change-reason").wait_for(state="visible", timeout=20000)
    page.locator("#wa-change-reason").fill("E2E test: raise weight on revenue signal.")
    page.locator(".wa-btn-primary").click()
    page.locator(".wa-alert-success").wait_for(state="visible", timeout=20000)


def t_weights_activate_admin(page: Page) -> None:
    # Depends on t_weights_propose_po having created an inactive draft earlier.
    login(page, "po")
    goto_view(page, "weights")
    page.locator("#wa-change-reason").wait_for(state="visible", timeout=20000)
    page.locator("#wa-change-reason").fill("E2E test draft for activation.")
    page.locator(".wa-btn-primary").click()
    page.locator(".wa-alert-success").wait_for(state="visible", timeout=20000)

    login(page, "admin")
    goto_view(page, "weights")
    activate = page.locator(".wa-btn-secondary", has_text="Activate")
    activate.first.wait_for(state="visible", timeout=20000)
    activate.first.click()
    page.locator(".wa-alert-success").wait_for(state="visible", timeout=20000)


def t_responsible_ai_renders(page: Page) -> None:
    login(page, "rm")
    goto_view(page, "responsible")
    page.locator(".rai-title").wait_for(state="visible", timeout=20000)
    assert page.locator(".rai-panel").is_visible()


TESTS: list[tuple[str, Callable[[Page], None]]] = [
    ("login_page_renders", t_login_page_renders),
    ("login_wrong_password", t_login_wrong_password),
    ("login_rm", t_login_rm),
    ("login_po", t_login_po),
    ("login_cr", t_login_cr),
    ("login_admin", t_login_admin),
    ("logout", t_logout),
    ("nav_all_views", t_nav_all_views),
    ("portfolio_list_renders", t_portfolio_list_renders),
    ("portfolio_source_filters", t_portfolio_source_filters),
    ("portfolio_band_filters", t_portfolio_band_filters),
    ("portfolio_search", t_portfolio_search),
    ("portfolio_select_company", t_portfolio_select_company),
    ("detail_score_now", t_detail_score_now),
    ("detail_all_tabs", t_detail_all_tabs),
    ("detail_generate_brief", t_detail_generate_brief),
    ("detail_ask_chat", t_detail_ask_chat),
    ("executive_renders", t_executive_renders),
    ("executive_row_click", t_executive_row_click),
    ("compare_toggle", t_compare_toggle),
    ("compare_max_three", t_compare_max_three),
    ("discovery_controls", t_discovery_controls),
    ("discovery_populate_button", t_discovery_populate_button),
    ("weights_readonly_rm", t_weights_readonly_rm),
    ("weights_propose_po", t_weights_propose_po),
    ("weights_activate_admin", t_weights_activate_admin),
    ("responsible_ai_renders", t_responsible_ai_renders),
]


def main() -> int:
    passed, failed = 0, 0
    failures: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS)
        for name, fn in TESTS:
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            page.set_default_timeout(20000)
            try:
                fn(page)
                print(f"PASS  {name}")
                passed += 1
            except (AssertionError, PWTimeout, Exception) as exc:  # noqa: BLE001
                failed += 1
                short = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
                print(f"FAIL  {name}  ->  {exc.__class__.__name__}: {short}")
                failures.append(name)
                if os.getenv("E2E_TRACE"):
                    traceback.print_exc()
            finally:
                context.close()
        browser.close()

    print("\n" + "=" * 56)
    print(f"E2E RESULT: {passed} passed, {failed} failed  (of {len(TESTS)})")
    if failures:
        print("Failing: " + ", ".join(failures))
    print("=" * 56)
    return failed


if __name__ == "__main__":
    sys.exit(main())
