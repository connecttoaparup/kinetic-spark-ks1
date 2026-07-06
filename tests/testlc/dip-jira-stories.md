# DIP AI-SDLC — All Jira Stories (One Epic, Build Order)

**How to use this file:** Create the Epic first (below). Then create each story
in order — the numbering is the order to build them. Create one, come back,
create the next. Each story block is copy-paste ready: Summary, Description,
Acceptance Criteria, Possible Input, Possible Output, Reference.

**Note:** The GitHub repos already exist, so the first story is about setting up
the STRUCTURE inside the existing central repo — not creating the repo.

---
---

# ============ THE EPIC ============

**Epic Summary:**
Build DIP Agentic AI-SDLC Platform

**Epic Description:**
Deliver an end-to-end agentic AI-SDLC for the Data Ingestion Platform. A
developer selects the `dip-ings-supervisor` agent in VS Code, gives it a Jira
story, and the platform plans the work, routes it to the right engineer agent,
builds the code/config in the correct repo, validates it, opens pull requests in
dependency order (with a cross-repo merge gate), and keeps the Jira story updated
throughout.

Scope: the central AI-tools repo (skills, agents, principles, CI gate); domain
skills for all four repo types (PySpark app, ingestion-config, Airflow plugin,
dag-config); the supervisor + engineer agents; connection to our existing local
Jira/GitHub MCP tools; and one proven end-to-end run for both a single-repo
ticket and a cross-repo new-asset ticket. We are productionizing an already-
working prototype, not building from scratch.

**Success criteria:**
Two real Jira stories complete fully through the flow — one single-repo change,
one cross-repo new data asset — each ending in Jira "Done" with pull requests
merged in the correct order.

---
---

# ============ STORIES (build order) ============

Points scale: 1 = tiny · 3 = ~half day · 5 = solid day+ · 8 = the big one.

---

## STORY 1 — Set up the folder structure in the central AI-tools repo
**Owner:** Developer 3 · **Points:** 3

**Description:**
The central repo (`dip-agentic-tools`) already exists on GitHub. This story sets
up the standard folder structure inside it, adds the reusable skill template, and
writes down the naming rules — so the whole team builds skills and agents
consistently. Everything else in this epic plugs into this structure.

**Acceptance Criteria:**
- [ ] The repo has these folders: `agents/`, `skills/` (with sub-folders
      `common/`, `app/`, `app-config/`, `dag/`, `dag-config/`), `.principles/`,
      `instructions/`, `templates/`, `tests/`, `.github/workflows/`.
- [ ] `templates/skill-template.md` exists showing the required format
      (frontmatter with `name`, `description`, `metadata`; a `## Workflow` and a
      `## Gotchas` section).
- [ ] `CONTRIBUTING.md` documents the naming rules: a skill's `name` field must
      equal its folder name; names are lowercase-with-hyphens; names are unique
      across ALL skill buckets.
- [ ] `AGENTS.md` at the repo root has the routing table (domain → repo → agent)
      and the hard rules (no hardcoded project IDs, confirm versions at runtime,
      barricade-migrate/tsql-to-bq are services not skills).
- [ ] `plugin.json`, `llms.txt`, and an initial `CHANGELOG.md` exist at the root.

**Possible Input:** the existing empty central repo.

**Possible Output:** the structured central repo, ready for skills/agents to be
added. Root contents:
```
dip-agentic-tools/
├── AGENTS.md  CONTRIBUTING.md  CHANGELOG.md  llms.txt  plugin.json
├── agents/  skills/  instructions/  .principles/  templates/  tests/
└── .github/workflows/
```

**Reference:** copy the structure from the prototype's `dip-agentic-tools/`
folder exactly.

---

## STORY 2 — Add the automatic skill checker (CI gate)
**Owner:** Developer 3 · **Points:** 3

**Description:**
Add a script that validates every skill file against the naming and format rules,
and make it run automatically on every pull request. This prevents broken or
wrongly-named skills from ever being merged.

**Acceptance Criteria:**
- [ ] `tests/test_skill_format.py` checks each `SKILL.md`: frontmatter present;
      `name` present, lowercase-hyphen, ≤64 chars; `name` equals its folder name;
      `description` present, ≤1024 chars; file ≤500 lines.
- [ ] The script also checks GLOBAL name uniqueness across all buckets and fails
      if two skills share a name.
- [ ] `.github/workflows/validate-skills.yml` runs this script on every pull
      request touching `skills/`, `agents/`, or `templates/`.
- [ ] Running locally prints `OK: N skills valid, names globally unique.` on
      success, and a clear list of problems on failure.

**Possible Input:** run `python tests/test_skill_format.py`.

**Possible Output (pass):**
```
OK: 10 skills valid, names globally unique.
```
**Possible Output (fail):**
```
SKILL VALIDATION FAILED:
  - skills/app/write-task/SKILL.md: name 'writetask' != dir 'write-task'
  - skills/dag-config/add-job/SKILL.md: duplicate name 'add-job'
```

**Reference:** `dip-prototype/dip-agentic-tools/tests/test_skill_format.py` —
already written and tested; copy as-is.

---

## STORY 3 — Write the "rules of the road" documents (principles + instructions)
**Owner:** Architect · **Points:** 3

**Description:**
Write the always-on guardrail documents the AI reads on every task: the
principles (architecture, security, anti-patterns) and one short per-repo
instructions file. These stop the AI from hardcoding project IDs, assuming
versions, or breaking layer boundaries.

**Acceptance Criteria:**
- [ ] `.principles/architecture.md`, `.principles/security.md`, and
      `.principles/app-config/anti-patterns.md` exist with concrete rules.
- [ ] One `instructions/<domain>/copilot-instructions.md` per repo type
      (app, app-config, dag, dag-config).
- [ ] Each per-repo instructions file is ALSO copied into that target repo's
      `.github/copilot-instructions.md` (the always-on per-repo layer).
- [ ] The anti-patterns file explicitly covers: three-part
      `${GCP_PROJECT}.dataset.table` unquoted; incremental/cdc require a
      watermark; cdc omits partition_col; job names globally unique.

**Possible Input:** (authored content — none)

**Possible Output:** a set of short markdown guardrail files the agents load
automatically, plus a copy of each in its target repo's `.github/`.

**Reference:** `dip-prototype/dip-agentic-tools/.principles/` and `instructions/`.

---

## STORY 4 — Inventory our real Jira tool names (from existing mcp.json)
**Owner:** Developer 3 · **Points:** 1

**Description:**
We already have Jira access set up locally in `mcp.json`. Our agents must call
Jira tools by their EXACT real names, or the calls silently do nothing. Find and
document the exact tool names our existing Atlassian MCP exposes.

**Acceptance Criteria:**
- [ ] Documented list of real Jira tool names for: fetch a story, update a story,
      update/transition a sub-task or its status.
- [ ] One example call per tool, with its required arguments.
- [ ] Confirmed reachable from VS Code (a test fetch of a real story returns
      data).

**Possible Input:** our existing `mcp.json` + the Atlassian MCP it points to.

**Possible Output (example doc):**
```
Server name in mcp.json: atlassian
Tools:
  - atlassian_get_issue(issue_key)                     -> story fields + status
  - atlassian_update_issue(issue_key, fields)          -> updates fields
  - atlassian_transition_issue(issue_key, transition)  -> moves status
```

**Reference:** the prototype uses placeholder `jira-ops/get_issue` etc. — this
story finds the REAL equivalents.

---

## STORY 5 — Inventory our real GitHub tool names (from existing mcp.json)
**Owner:** Developer 3 · **Points:** 1

**Description:**
Same as Story 4 but for GitHub — document the exact tool names for the pull-
request lifecycle from our existing `mcp.json`.

**Acceptance Criteria:**
- [ ] Documented real tool names for: create a PR, get a PR's status, merge a PR,
      list PRs.
- [ ] One example call per tool with required arguments.
- [ ] Confirmed reachable from VS Code (a test call returns data on a test repo).

**Possible Input:** our existing `mcp.json` + GitHub MCP.

**Possible Output (example doc):**
```
Server name in mcp.json: github
Tools:
  - github_create_pull_request(owner, repo, head, base, title, body)
  - github_get_pull_request(owner, repo, pull_number)  -> state: open|merged
  - github_merge_pull_request(owner, repo, pull_number)
```

**Reference:** prototype's placeholder `github/create_pull_request` etc.

---

## STORY 6 — "Write a PySpark task" skill
**Owner:** Developer 1 · **Points:** 3

**Description:**
Build the skill that generates a new ingestion Task class the standard way,
registers it in the TaskFactory, and creates a matching unit test. It must
confirm the PySpark version first (3.5 vs 4.x differ) and know that
barricade-migrate / tsql-to-bq are SERVICES of the app, not skills or tasks.

**Acceptance Criteria:**
- [ ] `skills/app/write-task/SKILL.md` passes the CI gate.
- [ ] Following the skill produces a Task subclass whose `execute()` returns
      `Tuple[TaskStatus, Optional[Exception]]` and never raises.
- [ ] The new task is registered in `task_factory.py`.
- [ ] A matching unit test file is generated.
- [ ] The skill instructs the agent to confirm the PySpark version before
      version-sensitive code.
- [ ] `## Gotchas` states: never `SparkSession.builder` directly; barricade/tsql
      are services, not tasks.

**Possible Input:**
```
write a task called CustomerDedup that removes duplicate customer rows
```
**Possible Output:** `etl/pipeline/customer_dedup.py` (Task subclass) +
registration in `task_factory.py` + `unit_tests/.../test_customer_dedup.py`.

**Reference:** `dip-prototype/.../skills/app/write-task/SKILL.md`.

---

## STORY 7 — "Add an ingestion job" skill + its checker
**Owner:** Developer 1 · **Points:** 5

**Description:**
Build the most-used config skill: it writes an ingestion job's YAML (plan), runs
a checker script that catches mistakes (validate), then saves it (execute). The
checker is a standalone Python script the skill calls.

**Acceptance Criteria:**
- [ ] `skills/app-config/add-job/SKILL.md` passes the CI gate.
- [ ] `scripts/validate_job.py` enforces: required keys present; `target_bq_table`
      is three-part `${GCP_PROJECT}.dataset.table` and NOT quoted; `load_mode` in
      {full, incremental, cdc}; incremental/cdc require `watermark_col`; cdc omits
      `partition_col`; `source` exists (case-sensitive) in the source registry.
- [ ] The skill follows plan → validate → execute (temp file → validate → only
      then move into `configs/jobs/<source>/<job>.yaml`).
- [ ] A known-bad job is rejected with a clear reason; a good one passes.

**Possible Input:**
```
add a job to ingest the CRM customers table into BigQuery, incremental on updated_at
```
**Possible Output (good job YAML):**
```yaml
source: CRM
job_name: crm_customers
target_bq_table: ${GCP_PROJECT}.crm.customers
load_mode: incremental
watermark_col: updated_at
partition_col: ingested_date
```
**Possible Output (checker rejecting a bad job):**
```
JOB INVALID (bad.yaml):
  - target_bq_table must NOT be quoted - ${GCP_PROJECT} resolves only when unquoted
  - load_mode 'incremental' requires watermark_col
```

**Reference:** `dip-prototype/.../skills/app-config/add-job/` (SKILL.md +
`scripts/validate_job.py`, both tested).

---

## STORY 8 — "Add SQL" and "Validate all config" skills
**Owner:** Developer 1 · **Points:** 3

**Description:**
Build the add-SQL skill (adds a transform file under `configs/sql/`) and the
repo-wide validation skill that runs the job checker across every job and catches
duplicate job names.

**Acceptance Criteria:**
- [ ] `skills/app-config/add-sql/SKILL.md` and
      `skills/app-config/validate-app-config/SKILL.md` pass the CI gate.
- [ ] add-sql writes a `.sql` file with a header comment (ticket, purpose, source
      job), references only three-part `${GCP_PROJECT}` tables, and uses no
      `SELECT *`.
- [ ] validate-app-config runs the job checker across all jobs and reports any
      duplicate `job_name` across files.

**Possible Input:**
```
add a SQL that enriches orders with customer segment and region
```
**Possible Output:** `configs/sql/orders_enrich.sql` with a header comment and an
explicit column list; then a repo-wide "all N jobs valid, no duplicate names"
report.

**Reference:** `dip-prototype/.../skills/app-config/add-sql/` and
`validate-app-config/`.

---

## STORY 9 — "Write an Airflow operator" skill (+ related DAG plugin skills)
**Owner:** Developer 2 · **Points:** 5

**Description:**
Build the write-operator skill (and closely related plugin skills) for the shared
Airflow plugin repo. Must confirm the Airflow version first (2.x vs 3.x differ)
and preserve backward compatibility since the plugin is shared by all projects.

**Acceptance Criteria:**
- [ ] `skills/dag/write-operator/SKILL.md` passes the CI gate.
- [ ] Following it scaffolds an operator under
      `plugins/dip_ingestion_plugin/operators/`.
- [ ] The skill instructs confirming the Airflow version before generating
      operator or provider-import code.
- [ ] `## Gotchas` states backward compatibility is mandatory (no removed/renamed
      params without a MAJOR bump + migration notes).

**Possible Input:**
```
write an operator that triggers an ingestion job by name
```
**Possible Output:** `plugins/dip_ingestion_plugin/operators/ingestion_operator.py`.

**Reference:** `dip-prototype/.../skills/dag/write-operator/SKILL.md`.

---

## STORY 10 — "Add a DAG" skill + checker (with cross-repo safety check)
**Owner:** Developer 2 · **Points:** 5

**Description:**
Build the add-DAG skill plus its checker. The important part: the checker must
confirm every job the DAG references actually exists (merged) in the ingestion-
config repo. This is the concrete enforcement of the cross-repo merge gate.

**Acceptance Criteria:**
- [ ] `skills/dag-config/add-dag/SKILL.md` passes the CI gate.
- [ ] `scripts/validate_dag_config.py`: validates JSON well-formed; requires
      `dag_id` + `schedule_interval`; requires each task to have `task_id` +
      `job_name`; confirms every `job_name` exists as a merged job YAML in the
      ingestion repo.
- [ ] A DAG referencing a real merged job passes; one referencing a missing job
      is rejected with a clear reason listing the known jobs.

**Possible Input:**
```
add a daily DAG that schedules crm_customers and crm_orders
```
**Possible Output (good DAG JSON):**
```json
{
  "dag_id": "daily_crm_dag",
  "schedule_interval": "@daily",
  "tasks": [
    {"task_id": "ingest_crm_customers", "job_name": "crm_customers"},
    {"task_id": "ingest_crm_orders", "job_name": "crm_orders"}
  ]
}
```
**Possible Output (checker rejecting a bad DAG):**
```
DAG INVALID (bad.json):
  - task 'b' references job 'crm_orders' which does NOT exist in the ingestion repo
    - cross-repo merge gate violation (known: ['crm_customers'])
```

**Reference:** `dip-prototype/.../skills/dag-config/add-dag/` (SKILL.md +
`scripts/validate_dag_config.py`, tested).

---

## STORY 11 — "Add a task to a DAG" and "Validate all DAGs" skills
**Owner:** Developer 2 · **Points:** 3

**Description:**
Build the add-task skill (appends a task to an existing DAG JSON) and the
repo-wide DAG validation skill.

**Acceptance Criteria:**
- [ ] `skills/dag-config/add-task/SKILL.md` and
      `skills/dag-config/validate-dag-config/SKILL.md` pass the CI gate.
- [ ] add-task appends `{task_id, job_name}` to an existing DAG and re-runs
      validation.
- [ ] validate-dag-config runs the DAG checker across all DAG files; dag_ids
      unique.

**Possible Input:**
```
add a task to daily_crm_dag that runs the crm_returns job
```
**Possible Output:** the updated `daily_crm_dag.json` with the new task,
re-validated.

**Reference:** `dip-prototype/.../skills/dag-config/add-task/` and
`validate-dag-config/`.

---

## STORY 12 — Build the 4 engineer agents
**Owner:** Architect · **Points:** 3

**Description:**
Write the four engineer agent personas (`.agent.md`), one per repo type. Each
knows its repo, which skills to route to, its rules, and how to open a PR.

**Acceptance Criteria:**
- [ ] `dip-ings-app-engineer`, `dip-ings-app-config-engineer`,
      `dip-ings-dag-engineer`, `dip-ings-dag-config-engineer` all exist under
      `agents/`.
- [ ] Each can be selected from the VS Code agent picker and does only its
      domain's work.
- [ ] Each creates a feature branch, commits with `<TICKET>: <summary>`, and opens
      a PR via the real GitHub tool.
- [ ] The app-config engineer hands off to the dag-config engineer when
      scheduling is implied.

**Possible Input:** a single-domain instruction, e.g. "add the crm_orders job".
**Possible Output:** the built change on a feature branch + an opened PR.

**Reference:** `dip-prototype/dip-agentic-tools/agents/dip-ings-*-engineer.agent.md`.

---

## STORY 13 — Supervisor agent + story-breakdown skill (THE BIG ONE)
**Owner:** Architect · **Points:** 8

**Description:**
Build the supervisor — the single front door for every ticket. It reads the
story, breaks it into subtasks (via the jira-story-breakdown skill), routes each
to the right engineer, and keeps Jira updated. It is ALWAYS the entry point, even
for a one-repo ticket (it still owns the Jira updates — it just does less). The
story-breakdown skill includes a plan-validator script.

**Acceptance Criteria:**
- [ ] `agents/dip-ings-supervisor.agent.md` exists and can be picked in VS Code.
- [ ] `skills/common/jira-story-breakdown/SKILL.md` passes the CI gate.
- [ ] `scripts/validate_plan.py` checks: valid domains; owner_agent + repo match
      the routing table; dependencies reference real subtasks; `depends_on_merge`
      true for cross-repo deps; no dependency cycles.
- [ ] For a SMALL story the plan has a single subtask (no forced decomposition).
- [ ] For a LARGE story the plan decomposes across repos with correct
      dependencies.
- [ ] Supervisor presents the plan and STOPS for human approval (gate #1), then
      writes the approved plan back to the Jira story.

**Possible Input:**
```
Start work on DIP-1234
```
**Possible Output (plan the supervisor presents):**
```
Plan for DIP-1234 (large: spans app-config + dag-config):
  DIP-1234-1 [app-config @ progectai-ingestion] add customers + orders jobs
  DIP-1234-2 [app-config @ progectai-ingestion] add orders enrichment SQL (needs -1)
  DIP-1234-3 [dag-config @ progectai-dag] daily DAG (needs -1,-2, waits for MERGE)
Approve? (no code written yet)
```

**Reference:** `dip-prototype/.../agents/dip-ings-supervisor.agent.md` +
`skills/common/jira-story-breakdown/` (SKILL.md + `scripts/validate_plan.py`,
tested).

---

## STORY 14 — Resumable state + cross-repo "wait for merge" gate
**Owner:** Architect · **Points:** 5

**Description:**
Two must-haves: (1) all progress is stored in the Jira story so the supervisor
can resume exactly where it stopped; (2) a cross-repo subtask is blocked until
the PR it depends on is actually merged.

**Acceptance Criteria:**
- [ ] Every state change (plan approved, subtask status, PR url) is written to the
      Jira story via the real Jira tool.
- [ ] "continue DIP-1234" re-reads the story (does NOT re-plan) and reports each
      subtask's status.
- [ ] A cross-repo subtask (`depends_on_merge: true`) is NOT dispatched until its
      dependency's PR shows merged (checked via the real GitHub tool).
- [ ] Stopping mid-story and resuming continues correctly with no lost work.

**Possible Input:**
```
continue DIP-1234
```
**Possible Output:**
```
DIP-1234-1: merged (progectai-ingestion#101)
DIP-1234-2: merged (progectai-ingestion#102)
DIP-1234-3: pending — cross-repo gate cleared (deps merged) → dispatching now
```

**Reference:** prototype supervisor's resume + dispatch rules; `validate_plan.py`
cross-repo checks.

---

## STORY 15 — Point all agents at our real Jira/GitHub tool names
**Owner:** Architect + Developer 3 · **Points:** 3

**Description:**
Update every agent file so it calls the real tool names from Stories 4 and 5
instead of the prototype's placeholders. Then prove a real Jira read and a real
GitHub PR both work end to end from an agent.

**Acceptance Criteria:**
- [ ] Every `.agent.md` `tools:` list uses the real tool names (no leftover
      `jira-ops/*` or `github/*` placeholders).
- [ ] The supervisor can read a real Jira story via the real tool.
- [ ] An engineer agent can open a real PR on a test repo via the real tool.
- [ ] A deliberately wrong tool name is shown to fail clearly (so silent failures
      are caught).

**Possible Input:** the tool-name docs from Stories 4 and 5; the agent files from
Stories 12–14.
**Possible Output:** agents that successfully make real Jira/GitHub calls.

**Reference:** prototype agent files under `dip-agentic-tools/agents/`.

---

## STORY 16 — VS Code setup files (workspaces + config)
**Owner:** Developer 3 · **Points:** 2

**Description:**
Create the VS Code config so a developer just opens the right workspace and
everything is wired: agents load by reference, our existing `mcp.json` is
connected, and there's one ready-to-open workspace per data asset plus a
full-platform one.

**Acceptance Criteria:**
- [ ] `.vscode/settings.json` points `chat.agentFilesLocations` at the central
      agents folder.
- [ ] Our existing `mcp.json` (Jira + GitHub) is connected in the workspace.
- [ ] One `<asset>.code-workspace` per asset opens that asset's ingestion + dag
      repos + the central repo together.
- [ ] A `full-platform.code-workspace` opens all five repos.
- [ ] Opening a workspace shows the supervisor in the agent picker and the tools
      available.

**Possible Input:** the repos cloned under one parent folder.
**Possible Output (example `progectai.code-workspace`):**
```json
{
  "folders": [
    { "path": "../progectai-ingestion" },
    { "path": "../progectai-dag" },
    { "path": "../dip-agentic-tools" }
  ],
  "settings": { "chat.agentFilesLocations": ["dip-agentic-tools/agents"] }
}
```

**Reference:** prototype `.vscode/settings.json` + `.vscode/mcp.json`.

---

## STORY 17 — Plug in "commit & raise PR" and "review PR" skills
**Owner:** Developer 1 · **Points:** 3

**Description:**
Wire the two lifecycle skills into the flow so that after code is written, the AI
commits it, fills the PR template, updates the changelog, opens the PR, and runs
an AI review — no manual steps.

**Acceptance Criteria:**
- [ ] `dip-commit-and-raise-pr` and `review-pr` skills pass the CI gate.
- [ ] commit-and-raise-pr: detects change type; writes a `<TICKET>: <summary>`
      commit; fills the PR template; updates CHANGELOG under `[Unreleased]`; opens
      the PR; then hands off to review-pr.
- [ ] The engineer agents use these skills automatically at the end of a build.

**Possible Input:**
```
commit and raise a PR for DIP-1234
```
**Possible Output:** a commit + filled PR body + CHANGELOG entry + an AI review
verdict, all in one flow.

**Reference:** the `dip-commit-and-raise-pr` SKILL + GUIDE already produced
(rename prefix to `dip-`).

---

## STORY 18 — Rename existing skills from "dip-" to "dip-"
**Owner:** Developer 1 (app) + Developer 2 (dag) · **Points:** 5 · **CUTTABLE**

**Description:**
Rename the skills we already use today from the `dip-` prefix to `dip-`, update
all references, and confirm they still pass the CI gate. Split across Dev 1 (app
+ app-config skills) and Dev 2 (dag + dag-config skills).

**Acceptance Criteria:**
- [ ] All existing skills use `dip-` names (folder + `name` field match).
- [ ] References to old names updated across the central repo.
- [ ] CI gate passes for all renamed skills.

**Possible Input:** the existing `dip-*` skills.
**Possible Output:** the same skills, renamed and passing.
**Reference:** naming rules in `CONTRIBUTING.md` (Story 1).
**Note:** First to cut if the sprint runs short — ship new `dip-` skills, migrate
old ones next sprint.

---

## STORY 19 — Full end-to-end test + demo runbook
**Owner:** Whole team (test) · Architect (runbook) · **Points:** 5

**Description:**
The sprint's proof. Run two real scenarios start to finish, confirm the
supervisor plans/routes/gates/closes both with Jira updated automatically, then
write the demo runbook and reset notes.

**Acceptance Criteria:**
- [ ] **Scenario A (single repo):** a config-only change goes story → plan
      (1 subtask) → build → PR → review → merge → Jira Done.
- [ ] **Scenario B (cross-repo new asset):** a new asset spanning ingestion + dag
      repos goes story → plan (multi subtask) → ingestion PRs merged first →
      cross-repo gate clears → dag PR → merge → Jira Done.
- [ ] In Scenario B, the dag work is provably blocked until the ingestion PRs
      merge.
- [ ] Both stories end in Jira "Done" with subtask statuses + PR urls recorded.
- [ ] A `DEMO-RUNBOOK.md` documents every step to run both scenarios from a clean
      state, plus reset/rollback steps.

**Possible Input:** two real Jira test stories (one single-repo, one new-asset).
**Possible Output:** two completed stories with real merged PRs + updated Jira +
a runbook someone else could follow.

**Reference:** the DIP-1234 walkthrough in the prototype README; `scripts/reset.py`.

---
---

## Order & assignment at a glance

| # | Story | Owner | Pts |
|---|---|---|---|
| 1 | Central repo structure | Dev 3 | 3 |
| 2 | CI gate | Dev 3 | 3 |
| 3 | Principles + instructions | Architect | 3 |
| 4 | Jira tool inventory | Dev 3 | 1 |
| 5 | GitHub tool inventory | Dev 3 | 1 |
| 6 | write-task skill | Dev 1 | 3 |
| 7 | add-job skill + checker | Dev 1 | 5 |
| 8 | add-sql + validate-app-config | Dev 1 | 3 |
| 9 | write-operator skill | Dev 2 | 5 |
| 10 | add-dag skill + checker | Dev 2 | 5 |
| 11 | add-task + validate-dag-config | Dev 2 | 3 |
| 12 | 4 engineer agents | Architect | 3 |
| 13 | Supervisor + breakdown (BIG) | Architect | 8 |
| 14 | Resume + merge gate | Architect | 5 |
| 15 | Point agents at real tools | Architect + Dev 3 | 3 |
| 16 | VS Code workspaces | Dev 3 | 2 |
| 17 | commit/review skills | Dev 1 | 3 |
| 18 | dip→dip rename (CUTTABLE) | Dev 1 + Dev 2 | 5 |
| 19 | End-to-end test + runbook | All / Architect | 5 |

**Totals:** Dev 1 ≈ 19 · Dev 2 ≈ 18 · Dev 3 ≈ 12 (+ pairing on 13/14) ·
Architect ≈ 22 + reviews.

**If short on time, cut in this order:** (1) Story 18 renames, (2) any validator
polish beyond acceptance criteria. Everything else is the minimum for a working
end-to-end demo.
