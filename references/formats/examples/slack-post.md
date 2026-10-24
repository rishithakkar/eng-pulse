# Slack post — preview

Rendered from `tests/fixtures/board_mismatch`. Fixture mode: this is a preview only and is never posted. In a live run this text goes to `slack_send_message_draft` first, and `slack_send_message` runs only after the user confirms.

```
*Acme engineering — Tue 27 Oct* · 🔴 0 · 🟡 2 · 🟢 0
🟡 *Payments v2* — merged work not yet closed on the board (1 flag)
🟡 *Mobile Onboarding* — code in review for an issue marked Todo (1 flag, _inferred_)

*Top flags*
1. 🟡 board_mismatch _inferred_ · <https://linear.app/acme/issue/GRO-205/otp-entry-screen|GRO-205> PR open, issue still Todo — Lena M: move GRO-205 to the state its code is in
2. 🟡 board_mismatch · <https://linear.app/acme/issue/PLT-106/card-tokenisation-vault|PLT-106> PR merged, issue still In Review — <@U0123ABC>: move PLT-106 to the state its code is in

_Coverage: all connectors connected · source: fixtures_
```

Notes on this render:

- Flag 1 comes first: both are yellow, and its evidence ([PR #11](https://github.com/acme/mobile-app/pull/11), opened 10h ago) is older than flag 2's ([PR #41](https://github.com/acme/payments-api/pull/41), merged 6h ago).
- Lena M has no Slack id in the team map, so her name is plain text with no mention; Priya S is mentioned as `<@U0123ABC>`.
- No Canvas: none was requested.
