# DIP Prototype — Developer Onboarding & Story Map

Read this once before you start your sprint story. It tells you **what in the
prototype is real (copy it), what is a laptop-only stand-in (do NOT copy it),**
and exactly **where your story's starting point lives.**

---

## 1. What this prototype is

It's a working, laptop-runnable reference implementation of the DIP AI-SDLC. It
proves the whole flow end-to-end with **no real credentials**. Almost every
sprint story already has a correct example inside it — your job is mostly to
**port and productionize**, not invent.

---

## 2. REAL vs STAND-IN (read this carefully)

| Part of the prototype | Status | What you do with it |
|---|---|---|
| `dip-agentic-tools/skills/**` | ✅ REAL | Copy/adapt into the central repo as-is |
| `dip-agentic-tools/agents/**` (logic & structure) | ✅ REAL | Copy; only the tool *names* change (see below) |
| `dip-agentic-tools/.principles/**` | ✅ REAL | Copy as-is |
| `dip-agentic-tools/instructions/**` | ✅ REAL | Copy as-is |
| `dip-agentic-tools/tests/test_skill_format.py` (CI gate) | ✅ REAL | Copy as-is |
| `**/scripts/validate_*.py` (all validators) | ✅ REAL | Copy as-is (they're standalone Python) |
| `.vscode/settings.json` (agents-by-reference) | ✅ REAL | Copy the pattern |
| **`mcp-servers/jira_ops.py`** | ⛔ STAND-IN | DELETE in production — use our real Atlassian MCP from `mcp.json` |
| **`mcp-servers/github_ops.py`** | ⛔ STAND-IN | DELETE in production — use our real GitHub MCP from `mcp.json` |
| **`mcp-servers/data/*.json`** | ⛔ STAND-IN | Fake Jira — real Jira replaces this |
| **Agent `tools:` names** (`jira-ops/*`, `github/*`) | ⚠️ PLACEHOLDER | Swap for our REAL tool names (story DIP-203) |
| `.vscode/mcp.json` (points at the fake servers) | ⚠️ PLACEHOLDER | Replace with our real `mcp.json` |

**Golden rule:** if it's a skill, agent-logic, validator, principle, or the CI
gate → it's real, copy it. If it touches Jira/GitHub *connection* → it's a
stand-in, and Epic B replaces it with what we already have.

---

## 3. Your story → where to start in the prototype

| Story | Owner | Start here in the prototype |
|---|---|---|
| DIP-101 central repo scaffold | Dev 3 | `dip-agentic-tools/` whole structure |
| DIP-102 CI gate | Dev 3 | `dip-agentic-tools/tests/test_skill_format.py` (copy as-is) |
| DIP-103 principles/instructions | Architect | `dip-agentic-tools/.principles/` + `instructions/` |
| DIP-201 Jira tool inventory | Dev 3 | *(prototype uses placeholders — you find the REAL names)* |
| DIP-202 GitHub tool inventory | Dev 3 | *(same — find the REAL names)* |
| DIP-203 point agents at real tools | Architect+Dev3 | `agents/*.agent.md` `tools:` lines |
| DIP-301 write-task skill | Dev 1 | `skills/app/write-task/SKILL.md` |
| DIP-302 add-job + checker | Dev 1 | `skills/app-config/add-job/` (SKILL + `scripts/validate_job.py`) |
| DIP-303 add-sql + validate-app-config | Dev 1 | `skills/app-config/add-sql/`, `validate-app-config/` |
| DIP-304 rename edh→dip (app) | Dev 1 | naming rules in `CONTRIBUTING.md` |
| DIP-401 write-operator | Dev 2 | `skills/dag/write-operator/SKILL.md` |
| DIP-402 add-dag + checker | Dev 2 | `skills/dag-config/add-dag/` (SKILL + `scripts/validate_dag_config.py`) |
| DIP-403 add-task + validate-dag-config | Dev 2 | `skills/dag-config/add-task/`, `validate-dag-config/` |
| DIP-404 rename edh→dip (dag) | Dev 2 | naming rules in `CONTRIBUTING.md` |
| DIP-501 four engineer agents | Architect | `agents/dip-ings-*-engineer.agent.md` |
| DIP-502 supervisor + breakdown | Architect | `agents/dip-ings-supervisor.agent.md` + `skills/common/jira-story-breakdown/` |
| DIP-503 resume + merge gate | Architect | supervisor dispatch rules + `validate_plan.py` |
| DIP-601 workspaces + config | Dev 3 | `.vscode/settings.json` (pattern) |
| DIP-602 commit/review skills | Dev 1 | the `edh-commit-and-raise-pr` SKILL + GUIDE (separate files) |
| DIP-603 end-to-end test | All | prototype README walkthrough (DIP-1234) |
| DIP-604 demo runbook | Architect | `scripts/reset.py` behavior |

---

## 4. How to run the prototype once (to understand it)

On any laptop with Python 3.9+ and git:

1. Unzip, open the folder in VS Code.
2. `python scripts/install_skills.py` (flat-installs skills — same as `gh skill install`).
3. Trust the two MCP servers when VS Code prompts (these are the STAND-IN ones).
4. Reload Window. Pick `dip-ings-supervisor` from the **agent picker dropdown**
   (NOT `@` — that's Visual Studio / CLI syntax).
5. Type `Start work on DIP-1234`, approve the plan, merge PRs when asked.
6. Reset any time with `python scripts/reset.py`.

Watch what it does — that IS the target behavior. Your production version does
the same thing but through our real Jira/GitHub instead of the stand-ins.

---

## 5. The one mistake to avoid

**Do not "productionize" `mcp-servers/jira_ops.py` or `github_ops.py`.** They
exist only so the prototype runs without credentials. In production we do not
host any MCP server — we use our existing local `mcp.json`. If you find yourself
editing those two files for production, stop: that work is actually DIP-201/202/203
(point the agents at the tools we already have).

---

## 6. Definition of Done (every story)

1. Passes the CI gate (`test_skill_format.py`) where applicable.
2. Its validator runs clean (if it has one).
3. Went through one real PR that passed AI review + human review.
4. If part of the flow, the supervisor used it successfully in an integration run.
