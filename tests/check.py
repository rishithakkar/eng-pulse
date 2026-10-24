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
