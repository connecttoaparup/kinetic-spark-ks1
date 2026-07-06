# DIP AI-SDLC — Local Prototype (Real Architecture)

A faithful, small-scale build of the **DIP (Data Ingestion Platform) agentic
AI-SDLC** you run with **real VS Code Copilot Chat agents** — no simulator.
Every layer is the production architecture:

| Layer | This prototype | Production |
|---|---|---|
| Central repo (source of truth) | `dip-agentic-tools/` | same repo at work |
| Agents | consumed **by reference** via `chat.agentFilesLocations` | same |
| Skills | flat install to `~/.copilot/skills` (what `gh skill install` does) | `gh skill install ... --pin v1.0.0` |
| jira-ops MCP | **real MCP server**, local stdio transport | same tool contract, Cloud Run HTTP |
| github MCP | **real MCP server** doing **real git branches & merges** | same tool contract, fronts github.com |
| Repos | 4 **real git repos** under `repos/` | 4 GitHub repos |
| State store | the Jira story via `jira-ops` tools | same |

The dev-stdio vs prod-HTTP MCP transport split is exactly what the platform
guide documents — the agents never know the difference.

---

## 1. Prerequisites

- **VS Code** (latest) with **GitHub Copilot + Copilot Chat** extensions, signed in
- **Python 3.9+** on PATH (`python --version`)
- **git** on PATH

## 2. Setup (one-time, ~2 minutes)

1. **Unzip** this folder anywhere, e.g. `C:\dev\dip-prototype`.
2. **Open the folder in VS Code**: File → Open Folder → `dip-prototype`.
3. **Install the skills to personal scope** (same flat layout `gh skill
   install` produces — skill names are globally unique for exactly this):
   ```bash
   python scripts/install_skills.py
   ```
   At work this step is: `gh skill install <org>/dip-agentic-tools --path skills --pin v1.0.0`
4. **MCP servers**: `.vscode/mcp.json` already defines `jira-ops` and
   `github` (stdio, Python). VS Code will ask you to **trust/start** them —
   accept. Verify via Command Palette → **MCP: List Servers** → both running.
5. **Agents**: `.vscode/settings.json` already points
   `chat.agentFilesLocations` at `dip-agentic-tools/agents` — the
   **consumption-by-reference** model. Reload Window
   (Ctrl+Shift+P → Reload Window) so Copilot discovers everything.

## 3. How to invoke the supervisor — important

**Not with `@`.** In VS Code, `@` is only for built-in participants
(`@workspace`, `@terminal`). Custom agents are selected from the **agent
picker dropdown** in the Copilot Chat panel — the same dropdown where
Ask / Edit / Agent modes live. Pick **`dip-ings-supervisor`** there.

(`@agent-name` works in Visual Studio 2026 the full IDE; in **Copilot CLI**
use `/agent dip-ings-supervisor` or `copilot --agent dip-ings-supervisor`.)

## 4. Running the demo — the full SDLC in chat

With **dip-ings-supervisor** selected, type:

```
Start work on DIP-1234
```

What you should see the supervisor do, in order:

1. **Fetch the story** — calls `jira-ops/get_issue("DIP-1234")` (watch the
   MCP tool call appear in chat).
2. **Plan** — activates the `jira-story-breakdown` skill: assesses the story
   (13 pts, spans app-config + dag-config → decompose), produces 3 subtasks
   with `repo`, `depends_on`, and `depends_on_merge=true` on the DAG subtask,
   validates the plan with `validate_plan.py`, and presents it.
3. **HUMAN GATE #1** — it stops and asks you to approve. Reply:
   ```
   approve
   ```
   It persists the plan via `jira-ops/update_issue` — the story is now the
   durable state store.
4. **Dispatch subtask 1** — hands off to **dip-ings-app-config-engineer**
   (click the handoff button, or tell it to proceed). The engineer:
   creates `feature/DIP-1234-crm-jobs` in `repos/progectai-ingestion`
   (real git branch), writes the two job YAMLs, runs the **add-job
   validator**, commits `DIP-1234: Add crm_customers...`, and opens
   **PR progectai-ingestion#101** via `github/create_pull_request`.
5. **HUMAN GATE #2** — "CODEOWNERS review — merge progectai-ingestion#101?"
   Reply `merge` → it calls `github/merge_pull_request` (a **real
   `git merge --no-ff` onto main** — check `git log` yourself) and records
   `merged` on the story via `jira-ops/set_subtask_status`.
6. **Subtask 2** (same repo, no merge gate needed) — orders enrichment SQL,
   same PR lifecycle → #102.
7. **CROSS-REPO MERGE GATE** — before subtask 3 (repo `progectai-dag`), the
   supervisor verifies #101/#102 are merged via `github/get_pull_request`.
   Only then does it hand off to **dip-ings-dag-config-engineer**, whose
   `add-dag` validator independently proves every referenced `job_name`
   exists merged in the ingestion repo.
8. **Done** — all subtasks merged, story marked Done, artifacts listed.

### The killer demo moment — resumability

Close the chat (or VS Code) any time mid-story. Open a new chat, select the
supervisor, and type:

```
continue DIP-1234
```

It re-reads the story via `jira-ops/get_issue` — **not** any chat memory —
reports each subtask's live status, and dispatches only what's unblocked.
That's "the Jira story is the state store," demonstrated.

## 5. Reset to run the demo again

```bash
python scripts/reset.py
```
Restores the story, the PR database, and hard-resets all four git repos to
their initial commit (deleting feature branches).

---

## 6. What's where

```
dip-prototype/                      <- open THIS folder in VS Code
├── AGENTS.md                          workspace always-on rules + routing
├── .vscode/
│   ├── settings.json                  agents by reference -> dip-agentic-tools/agents
│   └── mcp.json                       jira-ops + github MCP servers (stdio)
├── mcp-servers/
│   ├── jira_ops.py                    real MCP server (story state store)
│   ├── github_ops.py                  real MCP server (real git PRs/merges)
│   └── data/                          DIP-1234.json story + prs.json
├── scripts/                           install_skills.py | reset.py
├── dip-agentic-tools/                 THE CENTRAL REPO
│   ├── AGENTS.md · plugin.json · llms.txt · CHANGELOG.md · CONTRIBUTING.md
│   ├── agents/                        supervisor + 4 engineers (.agent.md)
│   ├── skills/                        10 skills, 5 buckets (common/app/
│   │                                  app-config/dag/dag-config)
│   ├── instructions/<domain>/         per-domain copilot-instructions
│   ├── .principles/                   architecture · security · anti-patterns
│   ├── templates/skill-template.md
│   ├── tests/test_skill_format.py     CI gate (also in .github/workflows/)
└── repos/                             FOUR REAL GIT REPOS
    ├── pyspark-ingestion-app/         FIXED shared app — barricade_migrate
    │                                  & tsql_to_bq are SERVICES here
    ├── composer/                      FIXED shared Airflow plugin
    ├── progectai-ingestion/           PROJECT-SPECIFIC app-config repo
    └── progectai-dag/                 PROJECT-SPECIFIC dag-config repo
```

Each repo carries its own `.github/copilot-instructions.md` (the always-on
per-repo layer), sourced from `dip-agentic-tools/instructions/<domain>/`.

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| Supervisor not in the agent picker | Reload Window. If still missing, VS Code may want absolute paths: in `.vscode/settings.json` change `chat.agentFilesLocations` to the full path of `dip-agentic-tools/agents`. |
| Skills never activate | Confirm `~/.copilot/skills/<name>/SKILL.md` exists (re-run `scripts/install_skills.py`), reload; you can force one with `/add-job` etc. in chat. |
| MCP tools missing | Command Palette → **MCP: List Servers** → start/trust both. Ensure `python` launches Python 3 on your PATH (else edit `.vscode/mcp.json` command to `py` or full path). |
| Agent asks to run terminal commands | Allow — engineers use real `git` + the skill validators via the execute tool. |
| Merge fails in github MCP | The feature branch must exist with commits before `create_pull_request` — that's by design. |

## 8. Prototype → production deltas (the only ones)

1. MCP transport: local **stdio** here → **Cloud Run HTTP** at work
   (`.vscode/mcp.json` URL entries instead of command entries). Tool
   contracts identical.
2. `github` MCP fronts local git here → github.com at work.
3. Skills install: `scripts/install_skills.py` here → `gh skill install
   ... --pin v1.0.0` at work.
4. Story data: `mcp-servers/data/` here → real Jira behind jira-ops at work.

Agents, skills, principles, instructions, validators, CI gate: **identical
artifacts, moved as-is.**
