# Identity resolution

How a name, login or id in a question, a connector payload or a report resolves to a `people` key or a project in the team map. Signals use the result as the flag owner (`references/signals.md`, *Owner resolution*); the `ask` skill uses it to understand who or what the user means.

## People

Resolve in this order and stop at the first single match:

1. **Exact `people` key** — `priya` → `priya`.
2. **`aliases`** — when a person entry carries an `aliases` list, an exact, case-insensitive match against it. The v1 schema gives people no `aliases` field, so in v1 this step applies only to projects; keep the step so later map versions slot in.
3. **Case-insensitive `name`** — `priya s` → the person whose `name` is `Priya S`. A first-name-only match counts only when exactly one person has that first name.
4. **Connector identity** — a Linear user id (`linear`), a GitHub login (`github`, compared case-insensitively) or a Slack id (`slack`). When a connector gives only an email (for example a Linear user from `list_users`, a Slack profile from `slack_read_user_profile`), match it to a person whose other connector profile shows the same email.
5. **Ask.** Several matches, or none: ask the user which person they mean, listing the candidates by `name`. Never guess, and never pick the first match silently.

When a connector identity resolves to nobody, the subject is still reported, but its owner is `null` and every format shows "unowned". Do not invent a person or edit the map; suggest running `setup` to add the mapping.

### Owner with no Slack id

A resolved owner without a `slack` field (for example `lena` in `team-map.example.yaml`) is shown by `name` as plain text: no mention, no `<@...>` link, no ping. The flag is otherwise unchanged. The same holds for a missing `github` or `linear` field: link the subject, never the person.

## Projects

Resolve in the same order:

1. Exact `name`.
2. `aliases`, case-insensitive (`pay-v2` → `Payments v2`).
3. Case-insensitive `name`.
4. Connector identity: `linear_project_id` (UUID), a repo in `repos`, or a channel in `slack_channels`.
5. Ask, listing candidate project names.

A resolved project is always queried by its `linear_project_id` UUID, never by name. A project that is not in the map is answered as "not in the team map"; it is not looked up by name in Linear, except `ask`'s one-time discovery search (`skills/ask`, step 3), which answers "not in the team map", never assigns a colour, and offers `setup refresh`.

## Teams

A person's team is the first team in the map whose `members` lists them. An issue's team is the team whose `linear_team_id` equals the issue's `team_id`. Team names resolve case-insensitively; anything else, ask.
