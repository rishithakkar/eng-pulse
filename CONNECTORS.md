# Connectors

eng-pulse reads three kinds of tool. Skills refer to them by category, so another tool can be slotted in later without rewriting the skills.

| Category | Placeholder | Included servers | Other options |
|---|---|---|---|
| Project tracker | `~~project tracker` | Linear (official connector, `mcp.linear.app`) | Jira, Asana — not yet supported |
| Source control | `~~source control` | GitHub (official remote MCP server, `https://api.githubcopilot.com/mcp/`, added as a custom connector) | GitLab — not yet supported |
| Chat | `~~chat` | Slack (official connector) | Microsoft Teams — not yet supported |

Linear is required. GitHub and Slack are optional: without them the report still runs and says which signals were omitted (see the coverage lines in `references/gather-github.md` and `references/gather-slack.md`).

## Linear and Slack

Add both from Claude's connector directory (Settings → Connectors) and sign in. No extra configuration. Make sure the Slack connector can see each channel listed in `slack_channels` in your `team-map.yaml`.

## GitHub

> **Not the built-in GitHub integration.** Claude.ai's built-in "GitHub integration" only syncs repository files into Projects. It cannot read pull requests, reviews, commits or checks, so eng-pulse treats it as "GitHub not connected". Connect GitHub's MCP server as a custom connector instead, using one of the routes below.

GitHub's MCP server does not support OAuth dynamic client registration, so the usual "add connector → sign in" flow fails. Use one of these:

### Route A (recommended): read-only token in a header

1. Create a **fine-grained personal access token** on GitHub: resource owner = your org, repository access = only the repos in your team map, permissions = read-only (Pull requests, Contents, Metadata, Actions, Commit statuses).
2. In Claude: Settings → Connectors → **Add custom connector**.
   - URL: `https://api.githubcopilot.com/mcp/readonly`
   - Authentication: **No sign in**
   - Request headers:
     - `Authorization: Bearer <your fine-grained read-only PAT>`
     - `X-MCP-Toolsets: pull_requests,repos,actions`
3. Start a chat and ask "list open PRs in `<org>/<repo>`" to confirm it works.

On Team and Enterprise plans a header credential on a shared connector is **used by every member** of the workspace. Scope the token to read-only on the relevant repos only, and rotate it like any shared secret.

A per-toolset URL form also exists, for example `https://api.githubcopilot.com/mcp/x/pull_requests/readonly`, if you prefer the URL to select the toolset instead of the header.

### Route B: your own GitHub OAuth App

Use this when each person should sign in as themselves.

1. On GitHub, register an **OAuth App** (org settings → Developer settings → OAuth Apps). Callback URL: `https://claude.ai/api/mcp/auth_callback` (community-reported, not yet confirmed in official docs — check it if sign-in fails).
2. In Claude: **Add custom connector**, URL `https://api.githubcopilot.com/mcp/readonly`, and choose **Use your own OAuth client**; paste the app's client id and secret.
3. An **org admin must approve the OAuth App** for the org, or private repos will be invisible.

### Tools eng-pulse uses

`search_pull_requests`, `list_pull_requests`, `pull_request_read`, `list_commits`, `search_issues`. The full allowlist per connector is `references/tool-names.json`.

## Checking what is connected

Every report ends with coverage lines. A line such as `GitHub not connected — ... omitted` means that connector was missing or could not be read; nothing else in the report is affected.
