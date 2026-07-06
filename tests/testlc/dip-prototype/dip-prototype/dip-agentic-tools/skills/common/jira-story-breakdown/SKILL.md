---
name: jira-story-breakdown
description: >
  Read a Jira story, assess its size and domain spread, and produce a
  structured execution plan that routes subtasks to the right DIP engineer
  agents. Use when starting work from a Jira story, or when asked to "break
  down", "plan", or "scope" a story. Produces a plan only - NEVER writes code.
metadata:
  domain: common
  owner: dip-platform
  version: "0.1"
---

# Jira Story Breakdown & Routing

You produce an execution PLAN. You never write application code.

## Workflow
1. READ the story via the jira-ops MCP tool: `jira-ops/get_issue(<STORY>)`.
2. ASSESS against references/sizing-rubric.md.
3. DECOMPOSE into domain-scoped subtasks with repo + depends_on +
   depends_on_merge (true when a dep lives in a DIFFERENT repo).
4. ROUTE each subtask to its owner_agent (see AGENTS.md routing table).
5. EMIT plan JSON; VALIDATE with scripts/validate_plan.py; loop until OK.
6. Present the plan and STOP for human approval.

## Gotchas
- Do NOT write code, even for a trivial story.
- A subtask belongs to exactly ONE domain; split if it spans two.
- Set depends_on so config exists (MERGED) before the DAG that schedules it.
