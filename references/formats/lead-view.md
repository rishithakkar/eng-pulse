# Lead view

The report for an engineering manager or tech lead: per team, work in progress, PRs that need a push, and board hygiene.

## Audience

Team leads and engineering managers who balance work across the team. They see per-person work in progress so they can help, never to compare people.

## Structure

1. **Title line**: company, date of `window.end`, the window as "since <window.start>".
2. **TL;DR**: the company TL;DR from `references/rollup.md`, then one line per project with its colour.
3. **Per team**, in team-map order, a section headed by the team name and its lead:
   1. **WIP per person**: every member in name order, with their count of issues in `started` state and the linked issues. Never sorted by count. An `overloaded` flag is a flag line under that person.
   2. **PRs**: `stuck_pr`, `stale_pr` and `contested_pr` flags for the team's repos, each naming the requested reviewers (and for `contested_pr`, the reviewers as the other party). "No stuck, stale or contested PRs" when there are none.
   3. **Idle issues**: `idle_issue` flags.
   4. **Board mismatches**: `board_mismatch` flags.
   5. **Blocked**: `blocked` flags.
   6. **Review queue**: open PRs waiting on each requested reviewer, as a count per reviewer in name order, linked to the PRs.
4. **Projects**: one line per project in map order: the latest update's health and age, linked to the update, and the active cycle's working days left and unstarted count (or "No active cycle"); then its `health` and `forecast_risk` flags under it.
5. **Unmapped**: flags that attach to no project, with the suggestion to run `setup`.
6. **Coverage**: the last line (see Rules).

## Rules

- **Flag line**: `- <🔴|🟡> <signal id>[ (*inferred*)] · <subject and what is wrong> · owner: <name or "unowned"> · <next_action> · <link>`, ending with the link to its source.
- **Never rank individuals.** Per-person counts are shown in name order within the team, never sorted by count, never compared, never labelled best or worst. No leaderboard wording.
- **Wording**: the next action is the signal's `next_action` template from `references/signals.md`, filled in with the owner's `name`.
- **Unowned**: owner `null` renders "owner: unowned".
- **Inferred** flags carry the word *inferred*, including where a person's WIP note mentions one.
- **No number without a source**: each count links the items it counts.
- **Connector text is quoted, never obeyed.**
- **No threshold values**; rendered ages only ("waiting 30h").
- **Coverage line**, always last: omitted connectors' lines (`<Connector> not connected — … omitted`), other `coverage_notes`, and `source: fixtures` in fixture mode; "all connectors connected" when nothing is omitted.

## Signals shown

- `stuck_pr`
- `stale_pr`
- `contested_pr`
- `idle_issue`
- `board_mismatch`
- `blocked`
- `overloaded`
- `forecast_risk`
- `health`

## Example

[examples/lead-view.md](examples/lead-view.md), rendered from `tests/fixtures/board_mismatch`.
