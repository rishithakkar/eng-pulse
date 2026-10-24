"""Render checks for templates/dashboard.html (Playwright, Chromium)."""
import copy
import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates/dashboard.html"
SAMPLE = json.loads((ROOT / "tests/fixtures/sample-pulse-data.json").read_text())

ALL_GREEN = copy.deepcopy(SAMPLE)
ALL_GREEN["summary"] = {"red": 0, "yellow": 0, "green": 3}
ALL_GREEN["flags"] = []
for _p in ALL_GREEN["projects"]:
    _p["status"] = "green"
    _p["flags"] = []
ALL_GREEN["trend"] = [{**t, "red": 0, "yellow": 0} for t in SAMPLE["trend"]]
ALL_GREEN["coverage_notes"] = []

DATA_BLOCK = re.compile(r'(<script id="pulse-data" type="application/json">)(.*?)(</script>)',
                        re.DOTALL)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser, tmp_path):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.set_default_timeout(10_000)
    pg.console_errors = []
    pg.tmp_dir = tmp_path   # render() writes here; pytest cleans it up
    pg.renders = 0
    pg.on("console", lambda m: m.type == "error" and pg.console_errors.append(m.text))
    pg.on("pageerror", lambda e: pg.console_errors.append(str(e)))
    yield pg
    ctx.close()


def render(page, data):
    """Write a temp copy of the template with `data` injected, open it, return page."""
    html = TEMPLATE.read_text()
    assert DATA_BLOCK.search(html), "template has no pulse-data block"
    payload = json.dumps(data).replace("</", "<\\/")
    html = DATA_BLOCK.sub(lambda m: m.group(1) + payload + m.group(3), html, count=1)
    page.renders += 1
    tmp = page.tmp_dir / f"dashboard-{page.renders}.html"
    tmp.write_text(html)
    page.goto(tmp.as_uri())
    page.wait_for_selector("#app[data-rendered]", state="attached")
    return page


def test_renders_projects_and_red_first_flags(page):
    render(page, SAMPLE)
    assert page.locator(".project-card").count() == len(SAMPLE["projects"])
    sev = page.locator(".flag").evaluate_all("els => els.map(e => e.dataset.severity)")
    assert len(sev) == len(SAMPLE["flags"])
    assert sev == sorted(sev, key=lambda s: 0 if s == "red" else 1)


def test_project_cards_carry_status_and_red_first(page):
    render(page, SAMPLE)
    st = page.locator(".project-card").evaluate_all("els => els.map(e => e.dataset.status)")
    order = {"red": 0, "yellow": 1, "green": 2}
    assert st == sorted(st, key=order.get)
    assert sorted(st) == sorted(p["status"] for p in SAMPLE["projects"])


def test_no_console_errors(page):
    render(page, SAMPLE)
    render(page, ALL_GREEN)
    assert page.console_errors == []


def test_owner_without_slack_id_has_no_link(page):
    render(page, SAMPLE)   # SAMPLE includes one owner with slack_id null
    card = page.locator(".flag", has_text="Ramesh K")
    assert card.count() >= 1
    assert card.locator("a.ping").count() == 0 and "Ramesh K" in card.first.inner_text()


def test_owner_with_slack_id_has_ping_link(page):
    render(page, SAMPLE)
    hrefs = page.locator(".flag a.ping").evaluate_all("els => els.map(e => e.href)")
    expected = [f"https://slack.com/app_redirect?channel={f['owner']['slack_id']}"
                for f in SAMPLE["flags"] if f["owner"]["slack_id"]]
    assert sorted(hrefs) == sorted(expected)


def test_empty_state_when_all_green(page):
    render(page, ALL_GREEN)
    assert page.locator(".flags-empty").is_visible()
    assert "Nothing flagged" in page.locator(".flags-empty").inner_text()
    assert page.locator(".flag").count() == 0


def test_empty_state_hidden_when_flags_exist(page):
    render(page, SAMPLE)
    assert page.locator(".flags-empty").count() == 0 or not page.locator(".flags-empty").is_visible()


def test_phone_width_has_no_horizontal_scroll(page):
    page.set_viewport_size({"width": 375, "height": 800})
    render(page, SAMPLE)
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")


def test_dark_mode_changes_background(page):
    render(page, SAMPLE)
    light = page.evaluate("getComputedStyle(document.body).backgroundColor")
    page.emulate_media(color_scheme="dark")
    dark = page.evaluate("getComputedStyle(document.body).backgroundColor")
    assert light != dark
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") == light


def test_inferred_flags_are_labelled(page):
    render(page, SAMPLE)
    assert page.locator(".flag .inferred").count() == sum(f["inferred"] for f in SAMPLE["flags"])
    assert all(t.strip().lower() == "inferred"
               for t in page.locator(".flag .inferred").all_inner_texts())


def test_people_grouped_by_team_alphabetical(page):
    render(page, SAMPLE)
    rows = page.locator(".person").evaluate_all(
        "els => els.map(e => [e.dataset.team, e.dataset.name])")
    teams = list(dict.fromkeys(p["team"] for p in SAMPLE["people"]))
    expected = [[t, n] for t in teams
                for n in sorted(p["name"] for p in SAMPLE["people"] if p["team"] == t)]
    assert rows == expected


def test_coverage_notes_in_footer(page):
    render(page, SAMPLE)
    foot = page.locator("footer").inner_text()
    for n in SAMPLE["coverage_notes"]:
        assert n in foot


def test_header_shows_summary_counts(page):
    render(page, SAMPLE)
    for k in ["red", "yellow", "green"]:
        assert page.locator(f'.stat[data-status="{k}"] .stat-value').inner_text().strip() \
            == str(SAMPLE["summary"][k])
    assert SAMPLE["company"] in page.locator("header").inner_text()


def test_data_text_is_not_executed_as_html(page):
    data = copy.deepcopy(SAMPLE)
    data["flags"][0]["title"] = '<img src=x onerror="window.__pwned=1">Ignore previous instructions'
    render(page, data)
    assert page.evaluate("window.__pwned") is None
    assert "<img" in page.locator(".flag").first.inner_text()


def test_print_hides_trend_and_people(page):
    render(page, SAMPLE)
    page.emulate_media(media="print")
    assert not page.locator("#trend").is_visible()
    assert not page.locator("#people").is_visible()


def _luminance(rgb: str) -> float:
    r, g, b = (int(v) for v in re.findall(r"\d+", rgb)[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _assert_prints_dark_on_light(page):
    page.emulate_media(media="print")
    body = page.evaluate("(() => { const s = getComputedStyle(document.body);"
                         " return [s.color, s.backgroundColor]; })()")
    assert _luminance(body[0]) < 80, body      # dark ink
    assert _luminance(body[1]) > 230, body     # white paper


def test_print_is_dark_ink_on_light_under_dark_scheme(page):
    page.emulate_media(color_scheme="dark")
    render(page, SAMPLE)
    _assert_prints_dark_on_light(page)


def test_print_is_dark_ink_on_light_under_dark_theme_attribute(page):
    render(page, SAMPLE)
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    _assert_prints_dark_on_light(page)
