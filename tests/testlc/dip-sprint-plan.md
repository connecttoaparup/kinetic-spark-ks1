# DIP AI-SDLC — One Sprint Plan (Full Jira Detail)

**Sprint length assumed:** 2 weeks (10 working days)
**Team:** 3 developers + 1 architect (you)
**Reference material every developer should read first:** the working prototype
(`dip-prototype/`) — it already contains a correct example of almost every story below.

**What we're building:** An AI helper inside VS Code that takes a Jira ticket and
walks it end-to-end — plans the work, writes the code/config, checks it, opens the
pull request, and updates Jira — across our 5 repositories.

**We are NOT starting from zero.** We have the prototype (reference model) and our
existing local Jira/GitHub access in `mcp.json`. Most stories are "productionize the
proven prototype," not "invent from scratch."

---

## Sprint Goal

> A developer opens VS Code, picks the `dip-ings-supervisor` agent, types "Start work
> on DIP-1234", and the platform plans, routes, builds, validates, opens PRs in the
> right order, and keeps Jira updated — for both a single-repo ticket and a cross-repo
> new-asset ticket.

## Lanes (who owns what)

- **Developer 1 — App lane:** PySpark app skills + ingestion-config skills + checkers.
- **Developer 2 — DAG lane:** Airflow plugin skills + dag-config skills + checkers.
- **Developer 3 — Plumbing lane:** central repo, CI gate, connect existing Jira/GitHub.
- **Architect (You):** supervisor + story-breakdown + merge gate + review all PRs.

---

## How to read each story

Every story has: **Description**, **Acceptance Criteria** (tick-box, testable),
**Possible Input** (what the developer/user gives it), **Possible Output** (what it
produces), and **Reference** (where in the prototype to look).

Points: 1 = tiny · 3 = ~half day · 5 = solid day+ · 8 = the big one.

---
---

# EPIC A — Foundation (must land Days 1–2; everyone depends on it)

---

## DIP-101 — Set up the central AI-tools repository
**Owner:** Developer 3 · **Points:** 3

**Description:**
Create the single central repository (`dip-agentic-tools`) that holds every AI skill
and agent for the platform. All other repos consume from here "by reference" — they do
not keep their own copies. This story establishes the folder structure, the naming
rules, and the reusable skill template so the whole team builds consistently.

**Acceptance Criteria:**
- [ ] Repo `dip-agentic-tools` exists with these folders: `agents/`, `skills/`
      (with sub-folders `common/`, `app/`, `app-config/`, `dag/`, `dag-config/`),
      `.principles/`, `instructions/`, `templates/`, `tests/`.
- [ ] `templates/skill-template.md` exists and shows the required format (frontmatter
      with `name`, `description`, `metadata`; a `## Workflow` and `## Gotchas` section).
- [ ] Naming rules are documented in `CONTRIBUTING.md`: a skill's `name` field must
      equal its folder name; names are lowercase-with-hyphens; names are unique across
      ALL buckets.
- [ ] `AGENTS.md` at the repo root contains the routing table (domain → repo → agent).

**Possible Input:** (none — this is scaffolding)

**Possible Output:** the empty-but-structured central repo, ready for others to add
skills into.

**Reference:** `dip-prototype/dip-agentic-tools/` — copy this structure exactly.

---

## DIP-102 — Add the automatic skill checker (CI gate)
**Owner:** Developer 3 · **Points:** 3

**Description:**
Add a script that validates every skill file against the rules, and make it run
automatically on every pull request to the central repo. This prevents broken or
wrongly-named skills from ever being merged.

**Acceptance Criteria:**
- [ ] `tests/test_skill_format.py` checks each `SKILL.md`: frontmatter present,
      `name` present + lowercase-hyphen + ≤64 chars, `name` equals its folder name,
      `description` present + ≤1024 chars, file ≤500 lines.
- [ ] The script also checks **global name uniqueness** across all buckets and fails
      if two skills share a name.
- [ ] A GitHub Actions workflow runs this script on every pull request touching
      `skills/`, `agents/`, or `templates/`.
- [ ] Running it locally prints `OK: N skills valid, names globally unique.` on success
      and a clear list of problems on failure.

**Possible Input:** the `skills/` folder (run: `python tests/test_skill_format.py`).

**Possible Output (pass):**
```
OK: 10 skills valid, names globally unique.
```
**Possible Output (fail):**
```
SKILL VALIDATION FAILED:
  - skills/app/write-task/SKILL.md: name 'writetask' != dir 'write-task'
  - skills/app-config/add-job/SKILL.md: duplicate name 'add-job' (also skills/dag-config/add-job)
```

**Reference:** `dip-prototype/dip-agentic-tools/tests/test_skill_format.py` — already
written and tested; port it as-is.

---

## DIP-103 — Write the "rules of the road" documents
**Owner:** Architect · **Points:** 3

**Description:**
Write the always-on guardrail documents the AI reads on every task: the principles
(architecture, security, anti-patterns) and one short per-repo instructions file. These
are what stop the AI from hardcoding project IDs, assuming versions, or breaking layer
boundaries.

**Acceptance Criteria:**
- [ ] `.principles/architecture.md`, `.principles/security.md`, and
      `.principles/app-config/anti-patterns.md` exist and state concrete rules.
- [ ] One `instructions/<domain>/copilot-instructions.md` exists per repo type
      (app, app-config, dag, dag-config).
- [ ] Each per-repo instructions file is also copied into that repo's
      `.github/copilot-instructions.md`.
- [ ] Anti-patterns file explicitly covers: three-part `${GCP_PROJECT}.dataset.table`
      (unquoted), incremental/cdc require watermark, cdc omits partition_col,
      job names globally unique.

**Possible Input:** (none — authored content)

**Possible Output:** a set of short markdown files the agents load automatically.

**Reference:** `dip-prototype/dip-agentic-tools/.principles/` and `instructions/`.

---
---

# EPIC B — Connect existing Jira & GitHub (NO new servers, all local)

> We already have Jira + GitHub working locally via `mcp.json` with our tokens. We build
> nothing new here — we just point the agents at the tools we already have.

---

## DIP-201 — Inventory our real Jira tool names
**Owner:** Developer 3 · **Points:** 1

**Description:**
Our agents must call Jira tools by their exact real names, or the calls silently do
nothing. Find and document the exact tool names our existing Atlassian MCP setup
exposes.

**Acceptance Criteria:**
- [ ] Documented list of the real Jira tool names for: fetch a story, update a story,
      update/transition a sub-task or its status.
- [ ] For each tool, one example call with its required arguments is written down.
- [ ] Confirmed these tools are reachable from VS Code (a test fetch of a real story
      returns data).

**Possible Input:** our existing `mcp.json` + the Atlassian MCP server it points to.

**Possible Output (example doc):**
```
Server name in mcp.json: atlassian
Tools:
  - atlassian_get_issue(issue_key)         -> story fields + status
  - atlassian_update_issue(issue_key, ...) -> updates fields
  - atlassian_transition_issue(issue_key, transition) -> moves status
```

**Reference:** prototype uses placeholder `jira-ops/get_issue` etc. — this story finds
the REAL equivalents.

---

## DIP-202 — Inventory our real GitHub tool names
**Owner:** Developer 3 · **Points:** 1

**Description:**
Same as DIP-201 but for GitHub — document the exact tool names for the pull-request
lifecycle.

**Acceptance Criteria:**
- [ ] Documented real tool names for: create a pull request, get a pull request's
      status, merge a pull request, list pull requests.
- [ ] One example call per tool with required arguments.
- [ ] Confirmed reachable from VS Code (a test call returns data on a test repo).

**Possible Input:** our existing `mcp.json` + GitHub MCP server.

**Possible Output (example doc):**
```
Server name in mcp.json: github
Tools:
  - github_create_pull_request(owner, repo, head, base, title, body)
  - github_get_pull_request(owner, repo, pull_number) -> state: open|merged
  - github_merge_pull_request(owner, repo, pull_number)
```

**Reference:** prototype's placeholder `github/create_pull_request` etc.

---

## DIP-203 — Point all agents at the real Jira/GitHub tool names
**Owner:** Architect + Developer 3 · **Points:** 3

**Description:**
Update every agent file so it calls the real tool names from DIP-201/202 instead of the
prototype's placeholders. Then prove a real Jira read and a real GitHub PR both work end
to end from an agent.

**Acceptance Criteria:**
- [ ] Every `.agent.md` `tools:` list uses the real tool names (no leftover
      `jira-ops/*` or `github/*` placeholders).
- [ ] The supervisor can read a real Jira story via the real tool.
- [ ] An engineer agent can open a real pull request on a test repo via the real tool.
- [ ] A mismatch test: a deliberately wrong tool name is shown to fail clearly (so we
      know silent-failures are caught).

**Possible Input:** the tool-name docs from DIP-201/202; the agent files from Epic E.

**Possible Output:** agents that successfully make real Jira/GitHub calls.

**Reference:** prototype agent files under `dip-agentic-tools/agents/`.

---
---

# EPIC C — App lane (Developer 1)

---

## DIP-301 — "Write a PySpark task" skill
**Owner:** Developer 1 · **Points:** 3

**Description:**
Build the skill that generates a new ingestion Task class the standard way, registers it
in the TaskFactory, and creates a matching unit test. It must confirm the PySpark version
first (3.5 vs 4.x differ) and know that barricade-migrate / tsql-to-bq are *services* of
the app, not skills or tasks.

**Acceptance Criteria:**
- [ ] `skills/app/write-task/SKILL.md` passes the CI gate (DIP-102).
- [ ] Following the skill produces a Task subclass whose `execute()` returns
      `Tuple[TaskStatus, Optional[Exception]]` and never raises.
- [ ] The new task is registered in `task_factory.py`.
- [ ] A matching unit test file is generated.
- [ ] The skill instructs the agent to confirm the PySpark version before writing
      version-sensitive code.
- [ ] `## Gotchas` states: never `SparkSession.builder` directly; barricade/tsql are
      services not tasks.

**Possible Input (what a user types):**
```
write a task called CustomerDedup that removes duplicate customer rows
```
**Possible Output:** `etl/pipeline/customer_dedup.py` (Task subclass) + registration in
`task_factory.py` + `unit_tests/.../test_customer_dedup.py`.

**Reference:** `dip-prototype/.../skills/app/write-task/SKILL.md`.

---

## DIP-302 — "Add an ingestion job" skill + its checker
**Owner:** Developer 1 · **Points:** 5

**Description:**
Build the most-used config skill: it writes an ingestion job's YAML (plan), runs a
checker script that catches mistakes (validate), then saves it (execute). The checker is
a standalone Python script the skill calls.

**Acceptance Criteria:**
- [ ] `skills/app-config/add-job/SKILL.md` passes the CI gate.
- [ ] `scripts/validate_job.py` exists and enforces: required keys present;
      `target_bq_table` is three-part `${GCP_PROJECT}.dataset.table` and NOT quoted;
      `load_mode` in {full, incremental, cdc}; incremental/cdc require `watermark_col`;
      cdc must omit `partition_col`; `source` exists (case-sensitive) in the source
      registry.
- [ ] The skill follows plan → validate → execute (writes to temp, validates, only then
      moves into `configs/jobs/<source>/<job>.yaml`).
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

## DIP-303 — "Add SQL" and "Validate all config" skills
**Owner:** Developer 1 · **Points:** 3

**Description:**
Build the add-SQL skill (adds a transform file under `configs/sql/`) and the repo-wide
validation skill that runs the job checker across every job and catches duplicate job
names.

**Acceptance Criteria:**
- [ ] `skills/app-config/add-sql/SKILL.md` and
      `skills/app-config/validate-app-config/SKILL.md` pass the CI gate.
- [ ] add-sql writes a `.sql` file with a header comment (ticket, purpose, source job)
      and references only three-part `${GCP_PROJECT}` tables; no `SELECT *`.
- [ ] validate-app-config runs the job checker across all jobs and reports any duplicate
      `job_name` across files.

**Possible Input:**
```
add a SQL that enriches orders with customer segment and region
```
**Possible Output:** `configs/sql/orders_enrich.sql` with a header comment and explicit
column list; then a repo-wide "all N jobs valid, no duplicate names" report.

**Reference:** `dip-prototype/.../skills/app-config/add-sql/` and `validate-app-config/`.

---

## DIP-304 — Rename existing app skills "edh-" → "dip-"
**Owner:** Developer 1 · **Points:** 5 · **CUTTABLE (see cut list)**

**Description:**
Rename the app-lane and app-config skills we already use today from the `edh-` prefix to
`dip-`, update all references, and confirm they still pass the CI gate.

**Acceptance Criteria:**
- [ ] All existing app/app-config skills use `dip-` names (folder + `name` field match).
- [ ] References to old names updated across the central repo.
- [ ] CI gate passes for all renamed skills.

**Possible Input:** the existing `edh-*` app skills.
**Possible Output:** the same skills, renamed and passing.
**Reference:** naming rules in `CONTRIBUTING.md` (DIP-101).

---
---

# EPIC D — DAG lane (Developer 2)

---

## DIP-401 — "Write an Airflow operator" (+ related DAG skills)
**Owner:** Developer 2 · **Points:** 5

**Description:**
Build the write-operator skill (and closely related plugin skills) for the shared
Airflow plugin repo. Must confirm the Airflow version first (2.x vs 3.x differ) and
preserve backward compatibility since the plugin is shared by all projects.

**Acceptance Criteria:**
- [ ] `skills/dag/write-operator/SKILL.md` passes the CI gate.
- [ ] Following it scaffolds an operator under
      `plugins/dip_ingestion_plugin/operators/`.
- [ ] The skill instructs confirming the Airflow version before generating operator or
      provider-import code.
- [ ] `## Gotchas` states backward compatibility is mandatory (no removed/renamed params
      without a MAJOR bump + migration notes).

**Possible Input:**
```
write an operator that triggers an ingestion job by name
```
**Possible Output:** `plugins/dip_ingestion_plugin/operators/ingestion_operator.py`.

**Reference:** `dip-prototype/.../skills/dag/write-operator/SKILL.md`.

---

## DIP-402 — "Add a DAG" skill + checker (with cross-repo safety check)
**Owner:** Developer 2 · **Points:** 5

**Description:**
Build the add-DAG skill plus its checker. **The important part:** the checker must
confirm every job the DAG references actually exists (merged) in the ingestion-config
repo. This is the concrete enforcement of the cross-repo merge gate.

**Acceptance Criteria:**
- [ ] `skills/dag-config/add-dag/SKILL.md` passes the CI gate.
- [ ] `scripts/validate_dag_config.py` exists and: validates JSON is well-formed;
      requires `dag_id` + `schedule_interval`; requires each task to have `task_id` +
      `job_name`; and confirms every `job_name` exists as a merged job YAML in the
      ingestion repo.
- [ ] A DAG referencing a real merged job passes; one referencing a missing job is
      rejected with a clear reason listing the known jobs.

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

## DIP-403 — "Add a task to a DAG" and "Validate all DAGs" skills
**Owner:** Developer 2 · **Points:** 3

**Description:**
Build the add-task skill (appends a task to an existing DAG JSON) and the repo-wide DAG
validation skill.

**Acceptance Criteria:**
- [ ] `skills/dag-config/add-task/SKILL.md` and
      `skills/dag-config/validate-dag-config/SKILL.md` pass the CI gate.
- [ ] add-task appends `{task_id, job_name}` to an existing DAG and re-runs validation.
- [ ] validate-dag-config runs the DAG checker across all DAG files; dag_ids unique.

**Possible Input:**
```
add a task to daily_crm_dag that runs the crm_returns job
```
**Possible Output:** the updated `daily_crm_dag.json` with the new task, re-validated.

**Reference:** `dip-prototype/.../skills/dag-config/add-task/` and `validate-dag-config/`.

---

## DIP-404 — Rename existing DAG skills "edh-" → "dip-"
**Owner:** Developer 2 · **Points:** 5 · **CUTTABLE**

**Description:** Same as DIP-304 but for the DAG lane.

**Acceptance Criteria:**
- [ ] All existing dag/dag-config skills use `dip-` names.
- [ ] References updated; CI gate passes.

**Possible Input / Output / Reference:** as DIP-304, DAG lane.

---
---

# EPIC E — The brain: agents & orchestration (Architect / You)

---

## DIP-501 — Build the 4 engineer agents
**Owner:** Architect · **Points:** 3

**Description:**
Write the four engineer agent personas (`.agent.md`), one per repo type. Each knows its
repo, which skills to route to, its rules, and how to open a PR.

**Acceptance Criteria:**
- [ ] `dip-ings-app-engineer`, `dip-ings-app-config-engineer`, `dip-ings-dag-engineer`,
      `dip-ings-dag-config-engineer` all exist under `agents/`.
- [ ] Each can be selected from the VS Code agent picker and does only its domain's work.
- [ ] Each creates a feature branch, commits with `<TICKET>: <summary>`, and opens a PR
      via the real GitHub tool.
- [ ] app-config engineer hands off to dag-config engineer when scheduling is implied.

**Possible Input:** a single-domain instruction, e.g. "add the crm_orders job".
**Possible Output:** the built change on a feature branch + an opened PR.
**Reference:** `dip-prototype/dip-agentic-tools/agents/dip-ings-*-engineer.agent.md`.

---

## DIP-502 — Supervisor agent + story-breakdown skill (THE BIG ONE)
**Owner:** Architect · **Points:** 8

**Description:**
Build the supervisor — the single front door for every ticket. It reads the story,
breaks it into subtasks (via the jira-story-breakdown skill), routes each to the right
engineer, and keeps Jira updated. It is ALWAYS the entry point, even for a one-repo
ticket (it still owns the Jira updates — it just does less). The story-breakdown skill
includes a plan-validator script.

**Acceptance Criteria:**
- [ ] `agents/dip-ings-supervisor.agent.md` exists and can be picked in VS Code.
- [ ] `skills/common/jira-story-breakdown/SKILL.md` passes the CI gate.
- [ ] `scripts/validate_plan.py` checks: valid domains; owner_agent + repo match the
      routing table; dependencies reference real subtasks; `depends_on_merge` set true
      for cross-repo deps; no dependency cycles.
- [ ] For a SMALL story the plan has a single subtask (no forced decomposition).
- [ ] For a LARGE story the plan decomposes across repos with correct dependencies.
- [ ] Supervisor presents the plan and STOPS for human approval (gate #1), then writes
      the approved plan back to the Jira story.

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
`skills/common/jira-story-breakdown/` (SKILL.md + `scripts/validate_plan.py`, tested).

---

## DIP-503 — Resumable state + cross-repo "wait for merge" gate
**Owner:** Architect · **Points:** 5

**Description:**
Two must-haves: (1) all progress is stored in the Jira story so the supervisor can
resume exactly where it stopped; (2) a cross-repo subtask is blocked until the PR it
depends on is actually merged.

**Acceptance Criteria:**
- [ ] Every state change (plan approved, subtask status, PR url) is written to the Jira
      story via the real Jira tool.
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
---

# EPIC F — Integrate & prove it works (whole team)

---

## DIP-601 — VS Code setup files (workspaces + config)
**Owner:** Developer 3 · **Points:** 2

**Description:**
Create the VS Code config so a developer just opens the right workspace and everything
is wired: agents load by reference, our existing `mcp.json` is connected, and there's
one ready-to-open workspace per data asset plus a full-platform one.

**Acceptance Criteria:**
- [ ] `.vscode/settings.json` points `chat.agentFilesLocations` at the central agents
      folder.
- [ ] Our existing `mcp.json` (Jira + GitHub) is connected in the workspace.
- [ ] One `<asset>.code-workspace` per asset opens that asset's ingestion + dag repos +
      the central repo together.
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

## DIP-602 — Plug in "commit & raise PR" and "review PR" skills
**Owner:** Developer 1 · **Points:** 3

**Description:**
Wire the two lifecycle skills into the flow so that after code is written, the AI
commits it, fills the PR template, updates the changelog, opens the PR, and runs an AI
review — no manual steps.

**Acceptance Criteria:**
- [ ] `edh-commit-and-raise-pr` (→ rename to `dip-`) and `review-pr` skills pass the CI
      gate.
- [ ] commit-and-raise-pr: detects change type, writes a `<TICKET>: <summary>` commit,
      fills the PR template, updates CHANGELOG under `[Unreleased]`, opens the PR, then
      hands off to review-pr.
- [ ] The engineer agents use these skills automatically at the end of a build.

**Possible Input:**
```
commit and raise a PR for DIP-1234
```
**Possible Output:** a commit + filled PR body + CHANGELOG entry + an AI review verdict,
all in one flow.

**Reference:** the `edh-commit-and-raise-pr` SKILL + GUIDE already produced this sprint.

---

## DIP-603 — Full end-to-end test on a real data asset (both ticket types)
**Owner:** Whole team · **Points:** 5

**Description:**
The sprint's proof. Run two real scenarios start to finish and confirm the supervisor
plans, routes, gates, and closes both, with Jira updated automatically.

**Acceptance Criteria:**
- [ ] **Scenario A (single repo):** a config-only change in the ingestion repo goes
      story → plan (1 subtask) → build → PR → review → merge → Jira Done.
- [ ] **Scenario B (cross-repo new asset):** a new asset spanning ingestion + dag repos
      goes story → plan (multi subtask) → ingestion PRs merged first → cross-repo gate
      clears → dag PR → merge → Jira Done.
- [ ] In Scenario B, the dag work is provably blocked until the ingestion PRs merge.
- [ ] Both stories end in Jira "Done" with subtask statuses + PR urls recorded.

**Possible Input:** two real Jira test stories (one single-repo, one new-asset).
**Possible Output:** two completed stories with real merged PRs and updated Jira.
**Reference:** the DIP-1234 walkthrough in the prototype README.

---

## DIP-604 — Demo runbook + rollback notes
**Owner:** Architect · **Points:** 2

**Description:**
Write the step-by-step demo script and the reset/rollback notes so the demo runs
smoothly and can be repeated.

**Acceptance Criteria:**
- [ ] A runbook lists every step to run both scenarios from a clean state.
- [ ] Reset/rollback steps are documented (how to return repos + Jira test stories to
      a clean state between runs).
- [ ] Someone who didn't build it can run the demo from the runbook alone.

**Possible Input:** the working platform.
**Possible Output:** `DEMO-RUNBOOK.md`.
**Reference:** prototype `scripts/reset.py` behavior.

---
---

## Workload summary

| Person | Stories | Points |
|---|---|---|
| Developer 1 | 301, 302, 303, 304, 602 | ~19 |
| Developer 2 | 401, 402, 403, 404 | ~18 |
| Developer 3 | 101, 102, 201, 202, 601 (+ pair on 203) | ~11 + pairing |
| Architect (You) | 103, 203, 501, 502, 503, 604 (+ all PR reviews) | ~24 |

Developer 3 is lightest (MCP-build work was removed) → they **pair with you on
DIP-502 / DIP-503**, the two hardest stories.

---

## Week-by-week

**Week 1 — Foundation + build the pieces**
- Days 1–2: DIP-101, 102, 103 done; DIP-201, 202 done. Nobody blocked — validators can
  be built from Day 1 (they're standalone Python).
- Days 3–5: each lane builds its skills in parallel; you build DIP-502.

**Week 2 — Connect + prove**
- Days 6–7: DIP-203 (real tool names), DIP-503 (resume + gate), DIP-601 (workspaces);
  do the edh→dip renames.
- Days 8–9: DIP-603 end-to-end test; fix breakages; DIP-602 commit/review wiring.
- Day 10: DIP-604 runbook + sprint review.

---

## If we run short — cut in THIS order

1. **DIP-304 + DIP-404** (edh→dip renames). Ship the new `dip-` skills; migrate the old
   ones next sprint.
2. Any "nice to have" polish on validators beyond the acceptance criteria.
3. Nothing else — everything else is the minimum for a working end-to-end demo.

---

## Definition of Done (applies to every story)

1. Passes the CI gate (name = folder, globally unique) where applicable.
2. Its validator runs clean (if it has one).
3. Went through one real PR that passed both AI review and human review.
4. If part of the flow, the supervisor successfully used it in an integration run.

---

## Two things to confirm before loading into Jira

1. **Sprint length:** this assumes 2 weeks. If 1 week, split at the Week 1 / Week 2 line
   into two sprints.
2. **Share the real `mcp.json` tool names** (Jira + GitHub) so DIP-201/202/203 are exact
   and we avoid a mid-sprint "why isn't the tool firing" surprise.
