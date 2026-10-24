# Changelog

All notable changes to eng-pulse are recorded here. Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-25

### Added

- `setup` skill: discovers Linear teams, projects and people (plus GitHub repos and Slack channels), proposes a mapping, confirms it in batches and writes a validated `team-map.yaml`; `setup refresh` shows only what changed.
- `daily-report` skill: exec brief, PM view, lead view and Slack post, delivered as a dashboard artifact, PDF, markdown or a draft-first Slack post; `--dry-run`.
- `ask` skill: ad-hoc answers about projects, epics, issues, people, what's stuck and what shipped, in prose with linked sources; declines to rank people.
- Signals rubric (`references/signals.md`) with nine signals: `stuck_pr`, `stale_pr`, `contested_pr`, `idle_issue`, `board_mismatch`, `blocked`, `overloaded`, `forecast_risk`, `health`; rollup rules in `references/rollup.md`.
- Gather recipes for Linear, GitHub and Slack, with one coverage line per missing connector.
- Self-contained dashboard template (light, dark and print) with a JSON Schema for its data.
- Fixture mode (`fixtures: <path>`) for offline runs, plus one fixture per signal with a near miss.
- Eval cases for all three skills, consistency checks (`tests/check.py`) and dashboard render tests.
- `CONNECTORS.md` with the GitHub custom-connector setup, and issue templates.
