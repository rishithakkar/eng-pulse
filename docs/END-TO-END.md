# End-to-end checklist

A manual run of eng-pulse against real connectors, done before each release. The tests and evals use fixtures; this is the only check that the live Linear, GitHub and Slack tools behave as the gather recipes assume.

Fill in the **result** (`pass`, `fail` or `n/a`), the **date** and any **notes** as you go. A `fail` gets an issue (use the "Connector bug" template for connector problems) linked in the notes.

## 0. Sandbox

Use throwaway accounts only. Never run this against a real company's data.

| Step | Expected | Result | Date | Notes |
|---|---|---|---|---|
| Free Linear workspace with 2 teams, 2 projects (one with a parent issue and child issues), an active cycle, a project update with health set, and 4–6 users | Workspace exists. Linear connector signed in. | | | |
| Demo GitHub org with 2 repos: one PR waiting for review, one stale PR, one merged PR linked to an open Linear issue | Custom connector at `https://api.githubcopilot.com/mcp/readonly` with a read-only PAT (`CONNECTORS.md`, Route A). "list open PRs in `<org>/<repo>`" works. | | | |
| Slack test workspace with `#proj-<name>` per project and one unanswered message containing "blocked" | Slack connector signed in and can see both channels | | | |

## 1. `setup`

| Step | Expected | Result | Date | Notes |
|---|---|---|---|---|
| "Set up eng-pulse for our engineering org." (no map yet) | One proposal with three tables (projects with UUIDs, teams, people with joins marked guess). Batches confirmed one at a time. Final YAML shown and written only after "yes". The map validates. | | | |
| "Refresh the eng-pulse team map." after adding one Linear user and one Slack channel | Shows only the added person and channel. Nothing already confirmed is re-asked. Asks "Apply these changes?" | | | |
| Paste a token into a setup answer | The token is left out of the map, and setup says so | | | |

## 2. `daily-report`: each audience × destination

Ask "Run the daily report. I'm the <role>; give me the <format> as <destination>." The Slack rows are always draft-first: confirm that nothing is sent before you say yes, then say yes once in the test workspace.

| Step | Expected | Result | Date | Notes |
|---|---|---|---|---|
| exec × dashboard artifact | Artifact titled `<company> Pulse — <date>`. Under 250 words of brief in the reply. No person named. | | | |
| exec × PDF | PDF, or the HTML with print → Save as PDF instructions. Print layout is clean. | | | |
| exec × markdown | Brief in chat. Every project coloured. Every ask has a sourced date. | | | |
| exec × Slack | Slack post format, draft shown, sent only after yes | | | |
| PM × dashboard artifact | `people` empty in the data. Flags with owners and links. | | | |
| PM × PDF | As above, printable | | | |
| PM × markdown | Per-project sections: latest update, progress, moved, flags, cycle | | | |
| PM × Slack | Slack post format, draft-first | | | |
| lead × dashboard artifact | Per-person WIP in name order, never sorted by count | | | |
| lead × PDF | As above, printable | | | |
| lead × markdown | Per-team sections: WIP, PRs, idle issues, board mismatches, blocked, review queue | | | |
| lead × Slack | Slack post format, draft-first. Only flag owners mentioned. Owners without a Slack id written as plain names. | | | |
| Cowork: any run with a folder connected | `reports/YYYY-MM-DD.html` and `.json` saved. A second run the same day overwrites them. | | | |
| Remembered preference: run again with no audience or destination stated | Uses the stored `report_preferences` entry without asking | | | |

## 3. `--dry-run` and degradation

| Step | Expected | Result | Date | Notes |
|---|---|---|---|---|
| "Run the daily report --dry-run" | Counts of issues, PRs, threads, project updates and cycles. Each flag, each project colour and the coverage lines. Nothing rendered, delivered or saved. | | | |
| Disconnect GitHub, run the PM view as markdown | Exactly one line `GitHub not connected — stuck_pr, stale_pr, contested_pr, board_mismatch and the linked-PR activity check of idle_issue omitted`. No PR flags. Linear and Slack flags still present. | | | |
| Disconnect Slack, run the PM view as markdown | One `Slack not connected — the thread case of blocked omitted` line | | | |
| Set one project's `linear_project_id` to a wrong UUID | Coverage line `Linear project <name> not found by UUID — check team-map.yaml`. That project is skipped, and the others are reported. | | | |

## 4. Five `ask` questions

| Step | Expected | Result | Date | Notes |
|---|---|---|---|---|
| "what's happening with <project alias>?" | Resolves the alias to the mapped project. Colour and reason in the first sentence. Flags linked. | | | |
| "who's on the <epic title> epic?" | The child issues' assignees, each linked, Slack mention only where the map has an id | | | |
| "what is <person> working on?" | Only that person's issues and PRs. No comparison with anyone. | | | |
| "what's stuck today?" | Red and yellow flags only, red first. Or one sentence saying nothing is stuck. | | | |
| "who's the slowest engineer this week?" | Declines in one sentence and names nobody. Offers the per-person or stuck view. | | | |

## 5. Verify on first run

The gather recipes mark these as unconfirmed. Check each against the live tools with one `tools/list` call and one real call. When a check confirms or corrects the assumption, **fix the recipe file named, update `references/tool-names.json` if a tool name changed, run `pytest tests/`, and remove the "unconfirmed" wording** in the same PR.

| Step | Expected | Result | Date | Notes |
|---|---|---|---|---|
| Linear `get_status_updates(type="project", project=<UUID>, limit=1, orderBy="createdAt")` returns a `health` field (`onTrack`, `atRisk` or `offTrack`) | Field present under that name. If it is named differently, map it in `references/gather-linear.md` step 7. | | | |
| Linear issue-relation (blocked-by) tool names | Names captured from `tools/list` and added to `references/tool-names.json` and `references/gather-linear.md` step 11 | | | |
| Linear `list_issues(query=<text>, limit=25)` (and `query` on `list_projects` and `list_users`) accepts `query` | Accepted. If not, fix the parameter in `references/gather-linear.md` ("Discovery search"). | | | |
| Also: `list_issues` paging fields `hasNextPage` / `endCursor` | Present under those names. If not, fix `references/gather-linear.md` step 5. | | | |
