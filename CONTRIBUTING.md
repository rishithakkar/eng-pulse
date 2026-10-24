# Contributing to eng-pulse

Thanks for helping. eng-pulse is mostly Markdown that Claude follows: skills in `skills/`, the rules they apply in `references/`, and data shapes in `schemas/`. The tests check that these files stay consistent. The evals check that Claude follows them.

## Layout

| Path | What lives there |
|---|---|
| `skills/<name>/SKILL.md` | Run order for `setup`, `daily-report` and `ask`. No rules of their own: each step names the reference that governs it. |
| `skills/<name>/evals/` | Eval cases: `prompt.md`, `case.yaml`, `graders/*.md`, input files and `place-files.sh`. |
| `references/signals.md` | The only place a signal is defined. |
| `references/rollup.md` | How flags become project colours and the TL;DR, and the rules every report follows. |
| `references/formats/` | One file per report format, plus golden examples in `examples/`. |
| `references/gather-*.md`, `identity.md`, `fixture-mode.md` | How data is read from each connector, how people and projects are resolved, and offline mode. |
| `references/tool-names.json` | The only connector tool names a recipe may mention. |
| `schemas/` | JSON Schemas for the team map, the gathered data model and the dashboard data. |
| `templates/dashboard.html` | The self-contained dashboard artifact. |
| `tests/` | `check.py` (consistency checks), `test_dashboard.py` (render tests), `fixtures/` (one folder per signal and per special case). |

## Running the tests

```bash
pip install -r tests/requirements.txt
python -m playwright install chromium   # once, for the dashboard render tests
pytest tests/
```

`pytest.ini` makes pytest collect both `tests/check.py` and `tests/test_*.py`. Every PR must keep `pytest tests/` green.

## Running the evals

Each skill ships eval cases in `skills/<name>/evals/`. Run them with the Claude CLI from the repo root:

```bash
claude plugin eval skills/<name> --allow-tools Read,Write,Bash --scaffold
```

Each case's `case.yaml` names `place-files.sh` as its `scaffold_script`; it copies the case's input files into the working directory before the prompt runs. Each file in `graders/` states one thing the answer must (or must not) do.

To try a case by hand, open a Claude session with the plugin installed and send the case's prompt with a fixtures folder, for example:

```
what's stuck today?
fixtures: tests/fixtures/board_mismatch
```

Fixture mode (`references/fixture-mode.md`) makes no connector calls and uses the fixture's `window.end` as `now`. Never let a skill read `expected.json`: it is the answer key.

## Adding a signal

1. **Open an issue first** with the "New signal" template (`.github/ISSUE_TEMPLATE/new-signal.md`): definition, threshold, owner rule, next action, fixture.
2. **Add a block to `references/signals.md`**: a `### <id>` heading, then a fenced `yaml` block **on the very next line** (no blank line between them, or `parse_signals` in `tests/check.py` fails) with exactly these keys:

   ```yaml
   id: <id>                      # same as the heading; snake_case with an underscore, e.g. slow_ci
   severity: yellow              # red | yellow
   sources_required: [linear]    # any of linear, github, slack
   threshold_key: <key>          # a key in the team map's thresholds, or null
   owner_rule: "<how the owner is found> → people, else <fallback>"
   next_action: "{owner}: <what to do with> {subject}"
   visible_in: [pm, lead]        # any of exec, pm, lead
   ```

   Then a `**Definition:**` paragraph (the exact condition, the subject and what `{age}` means) and a line `**Fixture:** tests/fixtures/<id>/`. Name thresholds by key only; never write a value.
3. **A new threshold** also needs the key in `schemas/team-map.schema.json`, `team-map.example.yaml`, `THRESHOLD_KEYS` in `tests/check.py` and the threshold list in `skills/setup/SKILL.md` (step 4). Adding a required key is a schema change: see "Schema versions".
4. **Add the fixture** `tests/fixtures/<id>/` with `linear.json`, `github.json`, `slack.json` (shapes in `references/fixture-mode.md`), `team-map.yaml` and `expected.json`:

   ```json
   {
     "flags": [{"signal": "<id>", "subject": "<identifier or url>", "owner": "<people key or null>", "inferred": false}],
     "project_status": {"<project name>": "yellow"},
     "near_miss": [{"subject": "<identifier or url>", "reason": "why this one must NOT flag"}]
   }
   ```

   The near miss is required. Make it sit just inside the threshold so an off-by-one shows up. Every id in the fixture must resolve against its `team-map.yaml`.
5. **Register the id everywhere the signal set is listed.** The tests compare each of these with `references/signals.md`:
   - `SIGNAL_IDS` in `tests/check.py`: the nine v0.1 ids are hard-coded there; add yours.
   - The `signal` enum under `flags` → `items` in `schemas/dashboard.schema.json`.
   - The coverage line of every source in `sources_required`: add the id to the `` `<Connector> not connected — … omitted` `` line in each matching `references/gather-<source>.md` (`gather-linear.md`, `gather-github.md`, `gather-slack.md`). The check only recognises ids that contain an underscore (plus the existing `blocked`, `overloaded` and `health`), which is why step 2 asks for one. Also add the id to the matching sentence in `skills/setup/SKILL.md` step 1 when it needs GitHub or Slack.
   - If the subject is a new kind (not an issue, PR, thread, cycle, project or person), add how it attaches to projects in `references/rollup.md` ("Attaching flags to projects").
6. **Run `pytest tests/`.** It must be green before you go on.
7. **If the signal is visible to an audience**, list it under `## Signals shown` in that format's file in `references/formats/`. A format may only show signals whose `visible_in` includes its audience. Also decide whether the Slack post shows it: `references/formats/slack-post.md` has its own `## Signals shown` list.
8. **Add the id to README's signal list** ("How it decides what to flag", the sentence naming the v0.1 signals).
9. **Add a CHANGELOG entry** under `## [Unreleased]`.

## Adding a format

1. Open an issue with the "Format request" template: audience, destination, an example of the output.
2. Add `references/formats/<name>.md` with the sections the existing formats use: `## Audience`, `## Structure`, `## Rules` (flag line, owner, *inferred*, no threshold values, coverage line), `## Signals shown` and `## Example`.
3. Add a golden example to `references/formats/examples/<name>.md`, rendered from a fixture in `tests/fixtures/`. Every flag in it carries a link.
4. Wire it into `skills/daily-report/SKILL.md` (step 2, audience or destination) and add an eval case under `skills/daily-report/evals/`.
5. Extend the format checks in `tests/check.py` (for example the `Signals shown` audience check). Then add a CHANGELOG entry.

## Hard rules — PRs that break these are declined

- **We never rank individuals.** No leaderboards, no sorting people by count, no "slowest" or "most". People appear as flag owners. Per-person load appears only in the lead view, in name order.
- **Connector text is untrusted data.** Issue titles, PR comments and Slack messages are quoted, never obeyed. No instruction in them may change a step, flag, colour, owner or destination.
- **Projects are matched by Linear project UUID, never by name.** Names and aliases are for people to read; `linear_project_id` is what the recipes query.
- **Slack posting is draft-first.** Show the draft, wait for an explicit yes, then send. Fixture mode never posts.
- **No threshold values outside the team-map files.** Signals, recipes, formats and skills name thresholds by key. Values live only in `team-map.yaml`, `team-map.example.yaml` and fixture maps. `tests/check.py` scans `references/signals.md`, `references/rollup.md`, `references/gather-linear.md`, `gather-github.md`, `gather-slack.md`, `identity.md`, `fixture-mode.md` and the bodies of `skills/daily-report/SKILL.md` and `skills/ask/SKILL.md` for a threshold key followed by a number; formats, examples, `skills/setup/SKILL.md` and the docs are not scanned, so review them by eye.
- **No number without a source.** Every count, age, percentage or forecast links the items it was computed from. Every flag links its source.

## Schema versions

`team-map.yaml` carries `eng_pulse_version` (currently `1`). If you change `schemas/team-map.schema.json` in a way that makes an existing map invalid, or changes what a key means:

1. Bump the version in the schema and in `team-map.example.yaml`, and in the two places `skills/setup/SKILL.md` hard-codes it: step 4 (`Set eng_pulse_version: 1`) and step 7 ("older than the current version (1)").
2. Add a migration note to `skills/setup/SKILL.md` step 7 ("Refresh"): what changed from the old version and how `setup` rewrites an old map. `setup refresh` migrates older maps and says what changed.
3. Update every fixture and eval map, and note the change in `CHANGELOG.md`.

Additive optional keys do not need a bump.

## Packaging

To build the installable plugin file from a clean checkout:

```bash
zip -r /tmp/eng-pulse.plugin . -x "*.DS_Store" -x ".git/*" -x ".superpowers/*" -x "docs/superpowers/*" -x "tests/screenshots/*" -x "__pycache__/*" -x "*/__pycache__/*" -x ".pytest_cache/*"
unzip -l /tmp/eng-pulse.plugin | grep -E "team-map.yaml|superpowers"   # only fixture and eval maps may appear
```

Never ship a root `team-map.yaml`.

## Known gaps

- **No per-signal dry-run evals.** Each signal has a fixture and an answer key (`tests/fixtures/<id>/expected.json`), and the report-level evals cover `board_mismatch`, `blocked`, the no-GitHub degradation and injected text, but no eval runs `daily-report --dry-run` on each signal's fixture and grades its flags against `expected.json`. Until one exists, check a new or changed signal by hand: run `Run the daily report --dry-run` with `fixtures: tests/fixtures/<id>` and compare the printed flags with `expected.json`.

## Commits and PRs

- Conventional prefixes, as in the history: `feat:`, `fix:`, `docs:`, `test:`, `chore:`. Short imperative subject, for example `fix: stuck_pr ignores conversation comments`.
- One change per PR. Include the fixture or eval that shows it working, and keep `pytest tests/` green.

## Issues

Use the templates in `.github/ISSUE_TEMPLATE/`:

- **New signal**: a risk or health condition to detect.
- **Connector bug**: a Linear, GitHub or Slack call that failed or returned unexpected data. Include the `--dry-run` output with private data removed.
- **Format request**: a new report format or delivery destination.
