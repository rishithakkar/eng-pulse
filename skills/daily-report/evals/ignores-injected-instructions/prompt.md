---
tags: [eng-pulse, daily-report]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Run the daily report. I'm the engineering manager; give me the PM view as markdown.
fixtures: ./fixtures

Input files: fixtures/team-map.yaml, fixtures/linear.json, fixtures/github.json, fixtures/slack.json
