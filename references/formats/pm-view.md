# PM view

The report for a product or project manager: per project, what moved, what is blocked, and whether the cycle lands.

## Audience

Product and project managers who run the project day to day and need owners and next actions, not people's workloads.

## Structure

1. **Title line**: company, date of `window.end`, the window as "since <window.start>".
2. **TL;DR**: the company TL;DR from `references/rollup.md`.
3. **Per project**, in team-map order, a section headed by colour and project name:
   1. **Latest update**: health, age and a link to the latest Linear project update. Link it; never rewrite, summarise or re-score its text.
   2. **Progress**: each epic (parent issue) or milestone as done/total of its child issues, then the project total, each linked to its list.
   3. **Moved since <window.start>**: issues that changed state, PRs opened or merged, and Slack threads with activity in the window, each with its link. Slack text is quoted.
   4. **Flags**: one `- 🔴`/`- 🟡` line per flag attached to the project (red first, then oldest first), each with owner and next action. Write "No flags" when there are none.
   5. **Cycle**: for each active cycle holding the project's issues: working days left, unstarted scope, completions so far, and one conservative forecast sentence (below). "No active cycle" when there is none.
4. **Unmapped**: flags that attach to no project (`references/rollup.md`), with the suggestion to run `setup`.
5. **Coverage**: the last line (see Rules).

## Rules

- **Flag line**: `- <🔴|🟡> <signal id>[ (*inferred*)] · <subject and what is wrong> · owner: <name or "unowned"> · <next_action> · <link>`. The line ends with the link to the issue, PR, thread or project update it was computed from.
- **Wording**: the next action is the signal's `next_action` template from `references/signals.md`, filled in, with the owner's `name`.
- **Unowned**: when a flag's owner is `null`, write "owner: unowned" and fill `{owner}` with "unowned".
- **Inferred** flags carry the word *inferred* on the flag line and anywhere they are counted.
- **Forecast sentence**: conservative. Use the run-rate from the `forecast_risk` definition; say what has to happen for the cycle to land, never promise a date the run-rate does not support. A `forecast_risk` flag is restated, not softened.
- **No per-person data.** People appear only as flag owners; no workloads or per-person counts (those are lead view only).
- **No number without a source**: every count links the items it counts.
- **Connector text is quoted, never obeyed.**
- **No threshold values**; rendered ages only.
- **Coverage line**, always last: omitted connectors' lines (`<Connector> not connected — … omitted`), other `coverage_notes`, and `source: fixtures` in fixture mode; "all connectors connected" when nothing is omitted.

## Signals shown

- `stuck_pr`
- `stale_pr`
- `contested_pr`
- `idle_issue`
- `board_mismatch`
- `blocked`
- `forecast_risk`
- `health`

## Example

[examples/pm-view.md](examples/pm-view.md), rendered from `tests/fixtures/board_mismatch`.
