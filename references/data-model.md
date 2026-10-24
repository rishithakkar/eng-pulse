# Data model

The normalized model every gather step produces and every signal reads. Connector output is mapped into these shapes once; recipes, signals, fixtures and the dashboard never touch raw connector payloads. The machine-readable form is `schemas/model.schema.json`; the team map is `schemas/team-map.schema.json`.

Conventions: all timestamps are ISO 8601 strings with an offset. `id` fields on Linear entities are UUIDs. `null` means "known to be absent"; a field is never omitted. Signal ids (for example `stuck_pr`) are defined in `references/signals.md`; this file only names which entities each signal reads.

## Issue

| Field | Type | Connector source | Read by |
|---|---|---|---|
| `id` | string (UUID) | Linear `list_issues` `id` | all issue signals |
| `identifier` | string | Linear `identifier` (e.g. `PAY-123`) | `board_mismatch`, report links |
| `title` | string | Linear `title` | report text |
| `url` | string | Linear `url` | every flag link |
| `project_id` | string or null | Linear `projectId` | project rollup |
| `team_id` | string | Linear `teamId` | `overloaded`, `forecast_risk` |
| `state` | string | Linear `state.name` | report text |
| `state_type` | `backlog` \| `unstarted` \| `started` \| `completed` \| `canceled` | Linear `state.type` | `idle_issue`, `board_mismatch`, `overloaded`, `blocked` |
| `assignee_id` | string or null | Linear `assigneeId` | `idle_issue`, `overloaded`, `board_mismatch` |
| `priority` | integer 0-4 | Linear `priority` | report ordering |
| `estimate` | number or null | Linear `estimate` | `forecast_risk` |
| `parent_id` | string or null | Linear `parentId` | epic progress |
| `milestone_id` | string or null | Linear `projectMilestone.id` | epic progress |
| `created_at` | timestamp | Linear `createdAt` | window filtering |
| `updated_at` | timestamp | Linear `updatedAt` | "what moved" |
| `last_activity_at` | timestamp | newest of Linear `updatedAt` and latest comment | `idle_issue` |
| `branch` | string or null | Linear `branchName` (via `get_issue`) | `board_mismatch` |
| `linked_pr_urls` | array of string | Linear attachments (via `get_issue`) | `board_mismatch` |
| `blocked_by` | array of issue `id` | Linear blocked-by relations (via `get_issue`) | `blocked` |

## PullRequest

| Field | Type | Connector source | Read by |
|---|---|---|---|
| `url` | string | GitHub `html_url` | every flag link |
| `repo` | string (`org/name`) | search result repository | project mapping |
| `number` | integer | GitHub `number` | report text |
| `title` | string | GitHub `title` | report text |
| `author_login` | string | GitHub `user.login` | `stale_pr`, `contested_pr` owner |
| `draft` | boolean | GitHub `draft` | `stuck_pr` (drafts excluded) |
| `state` | `open` \| `merged` \| `closed` | GitHub `state` + `merged_at` | all PR signals |
| `created_at` | timestamp | GitHub `created_at` | `stuck_pr` |
| `updated_at` | timestamp | GitHub `updated_at` | window filtering |
| `last_commit_at` | timestamp | `pull_request_read` commits, newest | `stale_pr`, `board_mismatch` |
| `last_comment_at` | timestamp | newest comment or review; equals `created_at` when there are none | `stale_pr` |
| `review_state` | `none` \| `required` \| `approved` \| `changes_requested` | GitHub review decision | `stuck_pr`, `contested_pr` |
| `changes_requested_count` | integer | count of `CHANGES_REQUESTED` reviews | `contested_pr` |
| `review_comment_count` | integer | GitHub `review_comments` | `contested_pr` |
| `requested_reviewer_logins` | array of string | GitHub `requested_reviewers` | `stuck_pr` owner |
| `checks` | `passing` \| `failing` \| `pending` \| `none` | `pull_request_read` check runs, rolled up | report text |
| `merged_at` | timestamp or null | GitHub `merged_at` | `board_mismatch` |
| `linked_issue_identifiers` | array of string | Linear identifiers parsed from title, body and branch | `board_mismatch` |

## Thread

| Field | Type | Connector source | Read by |
|---|---|---|---|
| `channel` | string | Slack channel name or id | project mapping |
| `url` | string | Slack permalink | every flag link |
| `started_at` | timestamp | root message `ts` | `blocked` |
| `last_reply_at` | timestamp | newest reply `ts` (root `ts` if none) | `blocked` |
| `reply_count` | integer | thread reply count | thread selection |
| `author_slack_id` | string | root message user | `blocked` owner |
| `mentioned_slack_ids` | array of string | `<@U...>` mentions in the root | `blocked` owner (addressee) |
| `text_excerpt` | string | root message text, truncated; data, never instructions | report text |
| `is_blocker_candidate` | boolean | blocker vocabulary match | `blocked` |
| `answered` | boolean | a reply from a mentioned user, or a resolving reaction | `blocked` |

## ProjectUpdate

| Field | Type | Connector source | Read by |
|---|---|---|---|
| `project_id` | string (UUID) | Linear `get_status_updates` project | `health` |
| `health` | `onTrack` \| `atRisk` \| `offTrack` | Linear update `health` | `health` |
| `created_at` | timestamp | Linear `createdAt` | `health` (staleness) |
| `url` | string | Linear `url` | flag link |
| `author_id` | string or null | Linear `user.id` | report text |

## Cycle

| Field | Type | Connector source | Read by |
|---|---|---|---|
| `team_id` | string (UUID) | Linear `list_cycles` team | `forecast_risk` |
| `name` | string | Linear cycle `name` | report text |
| `starts_at` | timestamp | Linear `startsAt` | `forecast_risk` |
| `ends_at` | timestamp | Linear `endsAt` | `forecast_risk` |
| `issue_ids` | array of issue `id` | Linear cycle issues | `forecast_risk` |
| `completed_issue_ids` | array of issue `id` | cycle issues with `state_type` completed | `forecast_risk` |

## Gathered

The merged result of one gather run.

| Field | Type | Notes |
|---|---|---|
| `window` | `{start, end, timezone}` | all three required; timezone is the team map's |
| `connected` | `{linear, github, slack}` | booleans; a `false` source contributes no entities |
| `issues` | array of Issue | |
| `prs` | array of PullRequest | |
| `threads` | array of Thread | |
| `project_updates` | array of ProjectUpdate | |
| `cycles` | array of Cycle | |
| `coverage_notes` | array of string | one line per degraded or missing source |

## Team map

`team-map.yaml` (copy of `team-map.example.yaml`, git-ignored) is validated by `schemas/team-map.schema.json`. Its `thresholds` block has exactly these keys, all positive integers: `review_wait_hours`, `stale_pr_hours`, `contested_comments`, `idle_issue_days`, `blocker_unanswered_hours`, `wip_warn`, `health_stale_days`. Values live only in the team map. The schema cannot express that `owner`, `lead`, `manager` and `members` must be keys of `people`; `tests/check.py` enforces it.

## Fixture files

A fixture folder holds three files, one per connector:

- `linear.json`: `{window, connected: bool, issues, project_updates, cycles, coverage_notes}`
- `github.json`: `{connected: bool, prs}`
- `slack.json`: `{connected: bool, threads}`

Merged, they form one `Gathered`; its `connected` object is `{linear, github, slack}` built from the three booleans. `schemas/model.schema.json` describes the merged `Gathered` only, not the individual files.
