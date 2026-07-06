---
name: review-pr
description: >
  Draft a PR body from the repo's pull_request_template and produce a
  lightweight AI review verdict for DIP prototype PRs. Use when a PR is opened
  or when asked to "review PR #N".
metadata:
  domain: common
  owner: dip-platform
  version: "0.1"
---

# Review PR (Prototype)

1. Read the diff and classify the change type.
2. Run domain validator for every touched config.
3. Emit verdict: APPROVE | APPROVE WITH SUGGESTIONS | CHANGES REQUESTED.

## Gotchas
- Never check a checklist box you have not verified by reading the file.
