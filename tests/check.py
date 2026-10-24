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
