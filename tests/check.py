"""Structural and behavioural checks for the eng-pulse plugin."""
import json
import re
from pathlib import Path

import jsonschema
import yaml


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (repo_root() / rel).read_text()


def load_yaml(path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def skill_dirs() -> list[Path]:
    return sorted(p for p in (repo_root() / "skills").glob("*/") if p.is_dir())


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    assert m, "missing YAML frontmatter"
    return yaml.safe_load(m.group(1)), m.group(2)


def test_plugin_manifest():
    m = json.loads(read(".claude-plugin/plugin.json"))
    assert m["name"] == "eng-pulse"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", m["name"])
    assert re.fullmatch(r"\d+\.\d+\.\d+", m["version"])
    assert m["license"] == "MIT"


def test_every_skill_has_frontmatter_and_short_body():
    dirs = skill_dirs()
    assert [d.name for d in dirs] == ["ask", "daily-report", "setup"]
    for d in dirs:
        fm, body = parse_frontmatter((d / "SKILL.md").read_text())
        assert fm["name"] == d.name
        assert len(fm["description"]) >= 60
        assert len(body.splitlines()) <= 150


def test_repo_hygiene_files_exist():
    for f in ["LICENSE", "CHANGELOG.md", "README.md", "CONTRIBUTING.md",
              ".github/ISSUE_TEMPLATE/new-signal.md",
              ".github/ISSUE_TEMPLATE/connector-bug.md",
              ".github/ISSUE_TEMPLATE/format-request.md"]:
        assert (repo_root() / f).exists(), f


def test_gitignore_protects_private_files():
    gi = read(".gitignore")
    assert "docs/superpowers/" in gi and "team-map.yaml" in gi


THRESHOLD_KEYS = {"review_wait_hours", "stale_pr_hours", "contested_comments",
                  "idle_issue_days", "blocker_unanswered_hours", "wip_warn",
                  "health_stale_days"}


def test_example_team_map_validates():
    schema = json.loads(read("schemas/team-map.schema.json"))
    jsonschema.validate(load_yaml(repo_root() / "team-map.example.yaml"), schema)


def test_example_team_map_cross_references_resolve():
    m = load_yaml(repo_root() / "team-map.example.yaml")
    people = set(m["people"])
    for p in m["projects"]:
        assert p["owner"] in people
    for t in m["teams"]:
        assert t["lead"] in people and t["manager"] in people
        assert set(t["members"]) <= people


def test_example_team_map_has_all_threshold_keys():
    m = load_yaml(repo_root() / "team-map.example.yaml")
    assert set(m["thresholds"]) == THRESHOLD_KEYS


def test_model_schema_is_valid_draft2020():
    jsonschema.Draft202012Validator.check_schema(json.loads(read("schemas/model.schema.json")))


# --- Task 3: signals rubric, rollup rules, fixtures ---------------------------

SIGNAL_IDS = {"stuck_pr", "stale_pr", "contested_pr", "idle_issue", "board_mismatch",
              "blocked", "overloaded", "forecast_risk", "health"}

SIGNAL_KEYS = {"id", "severity", "sources_required", "threshold_key", "owner_rule",
               "next_action", "visible_in"}


def parse_signals(path) -> dict[str, dict]:
    """Return {id: block} from every `### <id>` heading + fenced yaml block."""
    text = Path(path).read_text()
    headings = re.findall(r"^### (.+)$", text, re.MULTILINE)
    blocks = re.findall(r"^### (\S+)\n```yaml\n(.*?)\n```", text, re.MULTILINE | re.DOTALL)
    assert len(blocks) == len(headings), "every ### heading must be followed by a yaml block"
    out = {}
    for heading, body in blocks:
        block = yaml.safe_load(body)
        assert set(block) == SIGNAL_KEYS, (heading, set(block) ^ SIGNAL_KEYS)
        assert block["id"] == heading, heading
        assert heading not in out, f"duplicate signal {heading}"
        out[heading] = block
    return out


def merge_fixture(d) -> dict:
    """Merge a fixture folder's three connector files into one Gathered."""
    d = Path(d)
    lin = json.loads((d / "linear.json").read_text())
    gh = json.loads((d / "github.json").read_text())
    sl = json.loads((d / "slack.json").read_text())
    assert set(lin) == {"window", "connected", "issues", "project_updates", "cycles",
                        "coverage_notes"}, d
    assert set(gh) == {"connected", "prs"}, d
    assert set(sl) == {"connected", "threads"}, d
    gathered = {
        "window": lin["window"],
        "connected": {"linear": lin["connected"], "github": gh["connected"],
                      "slack": sl["connected"]},
        "issues": lin["issues"],
        "prs": gh["prs"],
        "threads": sl["threads"],
        "project_updates": lin["project_updates"],
        "cycles": lin["cycles"],
        "coverage_notes": lin["coverage_notes"],
    }
    jsonschema.validate(gathered, json.loads(read("schemas/model.schema.json")),
                        format_checker=jsonschema.FormatChecker())
    return gathered


def fixture_dirs() -> list[Path]:
    return sorted(p for p in (repo_root() / "tests/fixtures").iterdir() if p.is_dir())


def test_signals_file_defines_exactly_v1_set():
    assert set(parse_signals(repo_root() / "references/signals.md")) == SIGNAL_IDS


def test_every_signal_block_is_complete():
    thresholds = set(load_yaml(repo_root() / "team-map.example.yaml")["thresholds"])
    text = read("references/signals.md")
    for sid, s in parse_signals(repo_root() / "references/signals.md").items():
        assert s["severity"] in {"red", "yellow"}
        assert set(s["sources_required"]) <= {"linear", "github", "slack"}
        assert s["threshold_key"] is None or s["threshold_key"] in thresholds
        assert set(s["visible_in"]) <= {"exec", "pm", "lead"}
        assert "overloaded" != sid or s["visible_in"] == ["lead"]   # spec §7 hard rule
        assert (repo_root() / "tests/fixtures" / sid).is_dir()
        assert f"**Fixture:** tests/fixtures/{sid}/" in text


def test_every_fixture_is_well_formed():
    model = json.loads((repo_root() / "schemas/model.schema.json").read_text())
    tm = json.loads((repo_root() / "schemas/team-map.schema.json").read_text())
    for d in fixture_dirs():
        jsonschema.validate(merge_fixture(d), model)
        jsonschema.validate(load_yaml(d / "team-map.yaml"), tm)
        exp = json.loads((d / "expected.json").read_text())
        for f in exp["flags"]:
            assert f["signal"] in SIGNAL_IDS


def test_fixture_ids_resolve_against_their_team_map():
    for d in fixture_dirs():
        m, g = load_yaml(d / "team-map.yaml"), merge_fixture(d)
        people = m["people"]
        for p in m["projects"]:
            assert p["owner"] in people, d
        for t in m["teams"]:
            assert {t["lead"], t["manager"], *t["members"]} <= set(people), d
        linear_people = {p["linear"] for p in people.values() if "linear" in p}
        logins = {p["github"] for p in people.values() if "github" in p}
        slack_ids = {p["slack"] for p in people.values() if "slack" in p}
        projects = {p["linear_project_id"] for p in m["projects"]}
        teams = {t["linear_team_id"] for t in m["teams"]}
        issue_ids = {i["id"] for i in g["issues"]}
        for i in g["issues"]:
            assert i["assignee_id"] in linear_people | {None}, (d, i["identifier"])
            assert i["project_id"] in projects | {None}, (d, i["identifier"])
            assert i["team_id"] in teams, (d, i["identifier"])
            assert set(i["blocked_by"]) <= issue_ids and i["parent_id"] in issue_ids | {None}
        for pr in g["prs"]:
            assert {pr["author_login"], *pr["requested_reviewer_logins"]} <= logins, (d, pr["url"])
        for t in g["threads"]:
            assert {t["author_slack_id"], *t["mentioned_slack_ids"]} <= slack_ids, (d, t["url"])
        for u in g["project_updates"]:
            assert u["project_id"] in projects and u["author_id"] in linear_people | {None}
        for c in g["cycles"]:
            assert c["team_id"] in teams
            assert set(c["completed_issue_ids"]) <= set(c["issue_ids"]) <= issue_ids
        exp = json.loads((d / "expected.json").read_text())
        assert set(exp["project_status"]) == {p["name"] for p in m["projects"]}, d
        assert set(exp["project_status"].values()) <= {"red", "yellow", "green"}
        for f in exp["flags"]:
            assert set(f) == {"signal", "subject", "owner", "inferred"}, (d, f)
            assert isinstance(f["inferred"], bool), (d, f)
            assert f["owner"] is None or f["owner"] in people, (d, f)
        for n in exp.get("near_miss", []):
            assert set(n) == {"subject", "reason"} and n["reason"], (d, n)


def test_signal_fixtures_flag_their_own_signal_and_contain_a_near_miss():
    for sid in SIGNAL_IDS:
        exp = json.loads((repo_root() / "tests/fixtures" / sid / "expected.json").read_text())
        assert any(f["signal"] == sid for f in exp["flags"])
        assert exp["near_miss"]            # a subject that must NOT flag, with the reason


def test_special_fixtures():
    assert json.loads(read("tests/fixtures/all-green/expected.json"))["flags"] == []
    assert merge_fixture(repo_root() / "tests/fixtures/no-github")["connected"]["github"] is False
    assert "ignore" in read("tests/fixtures/untrusted-text/github.json").lower()


def test_rollup_doc_states_rules():
    r = read("references/rollup.md")
    for phrase in ["Red if any red", "Yellow if any yellow", "Green otherwise"]:
        assert phrase in r


def test_rubric_names_thresholds_never_values():
    text = read("references/signals.md") + read("references/rollup.md")
    for key in THRESHOLD_KEYS:
        assert not re.search(rf"{key}\W{{0,4}}\d", text), key


# --- Task 4: gather recipes, identity, fixture mode, connectors ---------------

FORBIDDEN_TOOL_NAMES = {"get_pull_request_reviews", "get_pull_request_status",
                        "get_pull_request", "list_project_updates", "create_comment"}


def test_recipes_use_only_allowlisted_tool_names():
    allow = json.loads(read("references/tool-names.json"))
    known = set().union(*(v for k, v in allow.items() if not k.startswith("_")))
    plausible = known | FORBIDDEN_TOOL_NAMES
    for c in ["linear", "github", "slack"]:
        text = read(f"references/gather-{c}.md")
        for bad in FORBIDDEN_TOOL_NAMES:
            assert not re.search(rf"\b{bad}\b", text), (c, bad)
        mentioned = set(re.findall(r"`([a-z_]+)`", text)) & plausible
        assert mentioned <= set(allow[c]) | known, (c, mentioned - known)


def test_linear_recipe_enforces_uuid_rule():
    t = read("references/gather-linear.md")
    assert "UUID" in t and "never by name" in t.lower()


def test_github_recipe_uses_search_qualifiers_and_degrades():
    t = read("references/gather-github.md")
    for q in ["org:", "is:pr", "is:open", "draft:false", "review:required", "updated:>="]:
        assert q in t
    assert "not connected" in t.lower()


def test_slack_recipe_lists_blocker_vocabulary():
    t = read("references/gather-slack.md")
    for w in ["blocked", "waiting on", "any update", "ETA"]:
        assert w in t


def test_every_recipe_has_produces_section_covering_model_fields():
    model_fields = {"issues", "prs", "threads", "project_updates", "cycles"}
    produced = set()
    for c in ["linear", "github", "slack"]:
        sec = read(f"references/gather-{c}.md").split("## Produces", 1)[1]
        produced |= {f for f in model_fields if f in sec}
    assert produced == model_fields


def test_connectors_md_has_github_setup_routes():
    t = read("CONNECTORS.md")
    assert "api.githubcopilot.com/mcp/readonly" in t
    assert "X-MCP-Toolsets" in t and "Bearer" in t and "OAuth" in t
    assert "~~project tracker" in t and "~~source control" in t and "~~chat" in t


def test_fixture_mode_contract():
    t = read("references/fixture-mode.md")
    for s in ["team-map.yaml", "linear.json", "github.json", "slack.json", "no connector calls"]:
        assert s in t


def test_recipe_coverage_lines_match_sources_required():
    sigs = parse_signals(repo_root() / "references/signals.md")
    for c, name in [("linear", "Linear"), ("github", "GitHub"), ("slack", "Slack")]:
        text = read(f"references/gather-{c}.md")
        line = re.search(rf"`{name} not connected — ([^`]+) omitted`", text)
        assert line, c
        needing = {s for s, b in sigs.items() if c in b["sources_required"]}
        listed = set(re.findall(r"[a-z]+_[a-z_]+|blocked|overloaded|health", line.group(1)))
        assert needing <= listed, (c, needing - listed)


def test_recipes_and_guides_name_thresholds_never_values():
    for f in ["gather-linear.md", "gather-github.md", "gather-slack.md", "identity.md",
              "fixture-mode.md"]:
        text = read(f"references/{f}")
        for key in THRESHOLD_KEYS:
            assert not re.search(rf"{key}\W{{0,4}}\d", text), (f, key)


# --- Task 5: report formats and golden examples -------------------------------

def parse_signals_shown(text: str) -> set[str]:
    """Signal ids from the bullet list under `## Signals shown`, up to the next `## `."""
    m = re.search(r"^## Signals shown\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert m, "missing ## Signals shown section"
    ids = set()
    for line in m.group(1).splitlines():
        b = re.match(r"\s*[-*]\s+`?([a-z_]+)`?", line)
        if b:
            ids.add(b.group(1))
    assert ids, "## Signals shown lists no signal ids"
    return ids


def test_formats_only_show_signals_allowed_for_their_audience():
    sig = parse_signals(repo_root() / "references/signals.md")
    for fmt, aud in [("exec-brief","exec"),("pm-view","pm"),("lead-view","lead")]:
        shown = parse_signals_shown(read(f"references/formats/{fmt}.md"))
        assert shown <= set(sig)
        for s in shown: assert aud in sig[s]["visible_in"]

def test_exec_example_under_250_words_and_names_no_people():
    ex = read("references/formats/examples/exec-brief.md")
    assert len(ex.split()) <= 250
    people = load_yaml(repo_root()/"tests/fixtures/board_mismatch/team-map.yaml")["people"]
    for p in people.values(): assert p["name"] not in ex

def test_lead_example_shows_wip_without_ranking():
    ex = read("references/formats/examples/lead-view.md").lower()
    assert "wip" in ex
    for w in ["top performer","lowest","ranked","leaderboard"]: assert w not in ex

def test_slack_post_is_draft_first_and_resolves_mentions():
    f = read("references/formats/slack-post.md")
    assert "draft" in f.lower() and "slack_send_message_draft" in f
    assert "no slack id" in f.lower()          # Review Focus 1 fallback rule

def test_every_flag_in_examples_carries_a_link():
    for fmt in ["pm-view","lead-view"]:
        ex = read(f"references/formats/examples/{fmt}.md")
        flag_lines = [l for l in ex.splitlines() if l.lstrip().startswith(("- 🔴","- 🟡"))]
        assert flag_lines and all("http" in l for l in flag_lines)


# --- Task 6: dashboard template and schema ------------------------------------

def test_sample_pulse_data_validates():
    jsonschema.validate(json.loads(read("tests/fixtures/sample-pulse-data.json")),
                        json.loads(read("schemas/dashboard.schema.json")))


def test_dashboard_schema_is_valid_draft2020_and_closed():
    schema = json.loads(read("schemas/dashboard.schema.json"))
    jsonschema.Draft202012Validator.check_schema(schema)
    flag_signal = schema["properties"]["flags"]["items"]["properties"]["signal"]
    assert set(flag_signal["enum"]) == SIGNAL_IDS

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False, node
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(schema)


def test_dashboard_is_self_contained():
    html = read("templates/dashboard.html")
    srcs = re.findall(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', html)
    # Google Fonts is the only external resource allowed; none at all is fine too.
    assert all(s.startswith("https://fonts.googleapis.com") or s.startswith("https://fonts.gstatic.com") for s in srcs)
    assert not re.search(r"@import\s+url\(\s*['\"]?https?://(?!fonts\.googleapis\.com)", html)
    assert 'id="pulse-data"' in html and "prefers-color-scheme: dark" in html
    assert ':root[data-theme="dark"]' in html and "@media print" in html


def test_dashboard_template_ships_the_sample_data():
    html = read("templates/dashboard.html")
    assert html.count('id="pulse-data"') == 1   # Claude's block swap must have one target
    m = re.search(r'<script id="pulse-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    assert m and json.loads(m.group(1)) == json.loads(read("tests/fixtures/sample-pulse-data.json"))
