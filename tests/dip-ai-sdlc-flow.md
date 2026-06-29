# DIP — Data Ingestion Platform · AI-SDLC Flow

Complete end-to-end flow: from a Jira story to merged PRs across multiple repos,
powered by the `dip-agentic-tools` skills & agents platform.

> **Golden Rule:** The Jira skill **PLANS** · The agents **BUILD** · Cross-repo deps wait for **MERGE** · Jira story is the **STATE STORE**

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 🤖 | Agent / Supervisor |
| 🛠️ | Skill |
| 🔌 | MCP Server |
| 🧑 | Human Gate |
| ⛔ | Cross-Repo Merge Gate |
| 🔶 | CI / Validation |
| 📄 | File Output |
| 📦 | Git Repo |

---

## Phase 0 — Developer Onboarding (One-time Setup)

> Install skills & agents from `dip-agentic-tools` by reference. No per-repo copies.

### Steps

| # | Action |
|---|--------|
| 1 | **Install skills:** `gh skill install dip-org/dip-agentic-tools --path .agents/skills --pin v1.0.0` → lands in `~/.copilot/skills/` with provenance metadata |
| 2 | **Point VS Code at agents:** set `chat.agentFilesLocations` to your local clone of `dip-agentic-tools/.agents/agents` |
| 3 | **Verify:** agents appear in the VS Code agent picker dropdown. Select from dropdown — no `@` prefix for custom agents |

### Input / Output

**Input:**
- Access to `dip-agentic-tools` repo
- VS Code with GitHub Copilot

**Output:**
- All 28 skills available in every repo (pinned to `v1.0.0`)
- 5 agent personas appear in VS Code picker
- `gh skill update` to upgrade when a new version is tagged

> 💡 **No per-repo copies.** Central repo is the single source of truth. Downstream repos consume by reference only.

---

## Phase 1 — Initiate: Start from Jira Story

> 🤖 `dip-ings-supervisor` selected in VS Code agent picker

### Steps

| # | Action |
|---|--------|
| 1 | Developer types: **"Start work on DIP-1234"** |
| 2 | Supervisor loads `AGENTS.md` + `copilot-instructions.md` (always-on layer) |
| 3 | Description match → activates 🛠️ `jira-story-breakdown` skill |
| 4 | 🔌 `jira-ops MCP` → `get_issue("DIP-1234")` fetches the full story |

### Input / Output

**Input:**
- Jira story ID: `DIP-1234`
- Developer prompt: `"Start work on DIP-1234"`

**Output:**
- Full story text in context
- Title, description, acceptance criteria

---

## Phase 2 — Plan: Assess, Decompose & Route

> 🛠️ `common/jira-story-breakdown` — produces a plan, **NO code written**

### Steps

| # | Action | Detail |
|---|--------|--------|
| 1 | **READ** | Story already in context from Phase 1 |
| 2 | **ASSESS** | Score against `references/sizing-rubric.md` — if >5 ACs / >8 pts / >1 source / spans domains → *large, decompose* |
| 3 | **DECOMPOSE** | Split into domain-scoped subtasks with `depends_on`, `repo`, `depends_on_merge` fields |
| 4 | **ROUTE** | Tag each subtask with `owner_agent` from routing table below |
| 5 | **EMIT** | Write `/tmp/DIP-1234-plan.json` |
| 6 | **VALIDATE** | Run `python scripts/validate_plan.py /tmp/DIP-1234-plan.json` — loop until `OK: plan is valid, acyclic, and cross-repo gates are correct.` |

### Routing Table

| Domain | Repo | Owner Agent |
|--------|------|-------------|
| `app` | `pyspark-ingestion-app` | `dip-ings-app-engineer` |
| `app-config` | `progectai-ingestion` | `dip-ings-app-config-engineer` |
| `dag` | `composer` | `dip-ings-dag-engineer` |
| `dag-config` | `progectai-dag` | `dip-ings-dag-config-engineer` |

### Sizing Rubric (summary)

Treat as **large / needs decomposition** if ANY of:
- Spans more than one domain, OR
- \> 5 acceptance criteria, OR
- Estimated > 8 story points, OR
- Touches > 1 source system or > 3 config files

### Input / Output

**Input:**
- Jira story context
- `references/sizing-rubric.md`
- Domain → repo → agent routing table

**Output:**
- `/tmp/DIP-1234-plan.json` (validated, acyclic)
- Validator exit `0`
- **Zero application code written**

### Example Plan JSON

```json
{
  "story": "DIP-1234",
  "title": "Onboard CRM customers + orders into BQ with daily DAG",
  "assessment": {
    "size": "large",
    "spans_domains": true,
    "spans_repos": true,
    "rationale": "Two tables + SQL transform in progectai-ingestion; DAG scheduling in progectai-dag."
  },
  "subtasks": [
    {
      "id": "DIP-1234-1",
      "summary": "Add ingestion jobs for customers + orders (incremental on updated_at)",
      "domain": "app-config",
      "repo": "progectai-ingestion",
      "owner_agent": "dip-ings-app-config-engineer",
      "skills": ["add-job"],
      "depends_on": [],
      "depends_on_merge": false,
      "status": "pending",
      "pr_url": null
    },
    {
      "id": "DIP-1234-2",
      "summary": "Add SQL transform enriching orders with customer attributes",
      "domain": "app-config",
      "repo": "progectai-ingestion",
      "owner_agent": "dip-ings-app-config-engineer",
      "skills": ["add-sql"],
      "depends_on": ["DIP-1234-1"],
      "depends_on_merge": false,
      "status": "pending",
      "pr_url": null
    },
    {
      "id": "DIP-1234-3",
      "summary": "Author daily DAG scheduling both jobs",
      "domain": "dag-config",
      "repo": "progectai-dag",
      "owner_agent": "dip-ings-dag-config-engineer",
      "skills": ["add-dag", "add-task"],
      "depends_on": ["DIP-1234-1", "DIP-1234-2"],
      "depends_on_merge": true,
      "status": "pending",
      "pr_url": null
    }
  ]
}
```

---

## 🧑 Human Gate — Plan Approval

> **No code is written until this gate passes.**

| Action | Detail |
|--------|--------|
| Supervisor presents plan | Subtask IDs, summaries, domains, repos, dependency order |
| Developer can **edit** | Change scope, merge subtasks |
| Developer can **reject** | Restart decomposition |
| Developer can **approve** | Proceed to dispatch |
| On approval | Supervisor writes each subtask `{id, repo, domain, status: pending}` to Jira story via 🔌 `jira-ops/update_issue` |

**Input:**
- The execution plan JSON
- Developer's review decision

**Output:**
- Approval signal
- Jira story updated with subtask state — **Jira is now the durable state store**

---

## Phase 4 — Build: Dispatch Subtasks 1 & 2 (Same Repo — progectai-ingestion)

> 🤖 `dip-ings-supervisor` handoff → 🤖 `dip-ings-app-config-engineer` (subagent, own context window)

### Subtask DIP-1234-1 — Add Ingestion Jobs

| # | Action |
|---|--------|
| 1 | Activates 🛠️ `add-job` |
| 2 | Gathers fields: source=`CRM`, job_name=`crm_customers`, load_mode=`incremental`, watermark_col=`updated_at` |
| 3 | Plans → writes `/tmp/crm_customers.yaml` |
| 4 | Validates: `python scripts/validate_job.py /tmp/crm_customers.yaml` — loop until pass |
| 5 | Executes → `configs/jobs/crm/customers.yaml` |
| 6 | Repeats for `orders.yaml` |
| 7 | Runs 🔶 `validate-app-config` (cross-file check) |

**Example output file — `configs/jobs/crm/customers.yaml`:**
```yaml
source: CRM
job_name: crm_customers
target_bq_table: ${GCP_PROJECT}.crm.customers
load_mode: incremental
watermark_col: updated_at
partition_col: ingested_date
```

### Subtask DIP-1234-2 — Add SQL Transform

> ⚡ **No merge gate** — same repo as subtask 1. May ride in the same PR.

| # | Action |
|---|--------|
| 1 | Activates 🛠️ `add-sql` |
| 2 | Plan → validate → execute → `configs/sql/orders_enrich.sql` |
| 3 | Runs 🔶 `validate-app-config` |

### PR & State Update

| Action | Detail |
|--------|--------|
| 🛠️ `review-pr` | Drafts PR body from `pull_request_template.md` |
| PR opened | `progectai-ingestion#101` (and/or `#102`) |
| State written | Supervisor writes `{status: in_review, pr_url}` to subtasks 1 & 2 in Jira |

### Input / Output

**Input:**
- Subtasks 1 & 2 from approved plan
- Source: CRM, load_mode: incremental, watermark_col: updated_at

**Output:**
- 📄 `configs/jobs/crm/customers.yaml`
- 📄 `configs/jobs/crm/orders.yaml`
- 📄 `configs/sql/orders_enrich.sql`
- PR `progectai-ingestion#101` opened
- Jira subtasks 1 & 2 → `status: in_review`

---

## 🧑 Human Gate — Code Review & Merge (progectai-ingestion)

| Action | Detail |
|--------|--------|
| CI runs | 🔶 `validate-app-config` + unit tests re-run in the repo pipeline |
| CODEOWNERS review | Reviewers for `progectai-ingestion` approve |
| PRs merged ✅ | `#101` / `#102` merged |
| State updated | Supervisor updates subtasks 1 & 2 → `status: merged` in Jira |

> ⏳ **The live CLI/Copilot session may end here.** That is by design — the cross-repo merge gate is now active and the Jira story holds all state. The developer resumes tomorrow with "continue DIP-1234".

**Input:**
- PRs `progectai-ingestion#101 / #102`
- CODEOWNERS approval

**Output:**
- PRs merged ✅
- Jira: subtasks 1 & 2 → `merged`
- Cross-repo gate for subtask 3 now openable

---

## Phase 6 — Cross-Repo Merge Gate: Resume & Gate Check

> ⛔ `depends_on_merge: true` — subtask 3 is in a **different repo** from its dependencies

### Jira as State Store (the resume point)

```
Jira story DIP-1234  ← single source of truth for run state
├── DIP-1234-1  repo: progectai-ingestion  status: merged  PR: #101
├── DIP-1234-2  repo: progectai-ingestion  status: merged  PR: #102
└── DIP-1234-3  repo: progectai-dag        status: pending (deps merged → ready)
```

### Resume Steps

| # | Action |
|---|--------|
| 1 | Developer: **"continue DIP-1234"** with `dip-ings-supervisor` selected |
| 2 | Supervisor reads story via 🔌 `jira-ops/get_issue` — **NOT** the stale `/tmp` plan |
| 3 | Checks PR merge status via 🔌 `github/get_pull_request` for deps 1 & 2 |
| 4 | Both `merged` → gate clears → dispatch subtask 3 |

### Dispatch Rule

```
For each subtask S in dependency order:
  if every dep of S is in the SAME repo as S:
      dispatch S as soon as deps are locally done   ← may share a PR
  else (S has a dep in a DIFFERENT repo):
      wait until that dep's PR status == merged      ← read from Jira + GitHub MCP
      only then dispatch S
  after S's PR opens: write {status, PR url} back to the Jira story
```

**Input:**
- `"continue DIP-1234"` developer prompt
- Jira story state (read via MCP)
- GitHub PR merge status (read via MCP)

**Output:**
- Gate cleared
- Subtask 3 dispatched to `dip-ings-dag-config-engineer`

---

## Phase 7 — Build: Dispatch Subtask 3 (Cross-Repo — progectai-dag)

> 🤖 `dip-ings-supervisor` handoff → 🤖 `dip-ings-dag-config-engineer` (subagent · progectai-dag working tree)

### Steps

| # | Action |
|---|--------|
| 1 | Activates 🛠️ `add-dag` — references the now-**merged** job names from progectai-ingestion |
| 2 | Plans → writes `/tmp/daily_crm_dag.json` |
| 3 | Activates 🛠️ `add-task` — adds tasks for `crm_customers` + `crm_orders` |
| 4 | Runs 🔶 `validate-dag-config` — loop until pass |
| 5 | Executes → `dags/daily_crm_dag.json` |
| 6 | 🛠️ `review-pr` drafts PR body → opens `progectai-dag#201` |
| 7 | Supervisor writes `{status: in_review, pr_url: progectai-dag#201}` to Jira subtask 3 |

**Example output — `dags/daily_crm_dag.json` (abbreviated):**
```json
{
  "dag_id": "daily_crm_dag",
  "schedule_interval": "@daily",
  "tasks": [
    { "task_id": "crm_customers", "job_name": "crm_customers" },
    { "task_id": "crm_orders",    "job_name": "crm_orders",
      "depends_on_past": false }
  ]
}
```

### Input / Output

**Input:**
- Subtask 3 from plan
- Merged job names from `progectai-ingestion` (now real, not tentative)
- Schedule: daily

**Output:**
- 📄 `dags/daily_crm_dag.json` (references merged job names, validated)
- PR `progectai-dag#201` opened
- Jira subtask 3 → `status: in_review`

---

## Phase 8 — Finalise: Review, Update Ticket & Merge

| Action | Detail |
|--------|--------|
| 🛠️ `jira-ticket-writer` | Posts all subtask statuses to DIP-1234 |
| Repo CI | 🔶 `validate-dag-config` + unit tests re-run in `progectai-dag` pipeline |
| CODEOWNERS review | Reviewers for `progectai-dag` approve |
| PR merged ✅ | `progectai-dag#201` merged |
| Story closed | Supervisor marks DIP-1234 Done in Jira |

**Input:**
- PR `progectai-dag#201`
- CODEOWNERS approval

**Output:**
- PR merged ✅
- Jira DIP-1234 → **Done**
- All 3 subtasks in `merged` state

---

## Phase 9 — Complete ✅

> DIP-1234 complete — 2 repos, 3 subtasks, 0 manually written boilerplate

### 📦 progectai-ingestion

| File | Status |
|------|--------|
| `configs/jobs/crm/customers.yaml` | ✅ merged PR #101 |
| `configs/jobs/crm/orders.yaml` | ✅ merged PR #101 |
| `configs/sql/orders_enrich.sql` | ✅ merged PR #102 |

### 📦 progectai-dag

| File | Status |
|------|--------|
| `dags/daily_crm_dag.json` | ✅ merged PR #201 |

> At no point did a skill write code. `jira-story-breakdown` produced a plan; the engineer agents,
> using their domain skills, produced all artifacts. That separation is what makes the system
> testable, auditable, and safe for management visibility.

---

## Skills Library — dip-agentic-tools

### 🌐 common/ — all repos (6 skills)

| Skill | Purpose |
|-------|---------|
| `jira-story-breakdown` | Read → assess → decompose → route. **Produces plan only.** |
| `jira-ticket-writer` | Writes and updates Jira tickets (needs evals) |
| `review-pr` | Drafts PR body from `pull_request_template.md` |
| `generate-docs` | Auto-generates documentation |
| `debug-pipeline` | Cross-domain pipeline debugging |
| `devops-infra-tickets` | Infrastructure and DevOps ticket creation |

### ⚡ app/ — PySpark ingestion app (7 skills)

| Skill | Purpose |
|-------|---------|
| `write-task` | Authors PySpark task classes |
| `write-service` | Authors PySpark service classes |
| `write-unit-test` | Scaffolds unit tests for PySpark code |
| `write-genai-app` | Authors GenAI application components |
| `tsql-to-bq` | Converts T-SQL to BigQuery SQL |
| `barricade-migrate` | Handles Barricade migration patterns |
| `validate-yaml-config` | Validates app YAML configuration |

### 📄 app-config/ — Ingestion YAML config (7 skills)

| Skill | Purpose |
|-------|---------|
| `pipeline-builder` | Builds ETL pipeline definitions (needs 4 fixes) |
| `add-environment` | Adds a new environment configuration |
| `add-job` | Adds a new ingestion job YAML |
| `add-pipeline` | Adds a new pipeline definition |
| `add-sql` | Adds a SQL transform config |
| `onboard-source` | End-to-end source onboarding |
| `validate-app-config` | Cross-file config validation |

### 🔧 dag/ — Airflow plugin framework (5 skills — NEW)

| Skill | Purpose |
|-------|---------|
| `write-operator` | 🆕 Authors custom Airflow operators |
| `write-sensor` | 🆕 Authors custom Airflow sensors |
| `write-airflow-service` | 🆕 Authors Airflow service classes |
| `write-generator` | 🆕 Authors DAG generator utilities |
| `debug-plugin` | 🆕 Debugs Airflow plugin framework issues |

### 📋 dag-config/ — DAG JSON config (7 skills)

| Skill | Purpose |
|-------|---------|
| `add-dag` | Adds a new DAG JSON config |
| `add-task` | Adds tasks to an existing DAG |
| `add-template` | Adds a DAG template |
| `debug-dag-config` | Debugs DAG config issues |
| `onboard-dag` | End-to-end DAG onboarding |
| `upgrade-plugin` | Upgrades DAG plugin version |
| `validate-dag-config` | Validates DAG JSON config |

---

## Agent Personas

| Agent | Domain | Repo | Key Skills | MCP |
|-------|--------|------|------------|-----|
| 🤖 `dip-ings-supervisor` | All · Entry point | — | `jira-story-breakdown`, `review-pr`, `jira-ticket-writer` | `jira-ops`, `github` |
| 🤖 `dip-ings-app-engineer` | PySpark | `pyspark-ingestion-app` | `write-task`, `write-service`, `write-unit-test`, `tsql-to-bq` | `pyspark-ops` |
| 🤖 `dip-ings-app-config-engineer` | YAML Config | `progectai-ingestion` | `add-job`, `add-sql`, `add-pipeline`, `onboard-source`, `validate-app-config` | — |
| 🤖 `dip-ings-dag-engineer` | Airflow Plugin | `composer` | `write-operator`, `write-sensor`, `write-airflow-service`, `debug-plugin` | — |
| 🤖 `dip-ings-dag-config-engineer` | DAG JSON | `progectai-dag` | `add-dag`, `add-task`, `upgrade-plugin`, `validate-dag-config` | — |

---

## Maturity Checklist

| # | Standard | Status |
|---|----------|--------|
| 1 | Four layers separated (instructions / principles / skills / agents) | ✅ Designed |
| 2 | All `SKILL.md` pass spec validation (name=dir, ≤64 chars, desc≤1024, ≤500 lines) | 🔨 CI gate |
| 3 | Skill names globally unique (flat-install safe) | 🔨 CI gate |
| 4 | Gold-standard template enforced for new skills | 🔨 Fix template first |
| 5 | Every skill has a Gotchas section grown from real corrections | 🔨 Per skill |
| 6 | Agent layer exists; personas route to skills + scope tools | 🔨 Build `.agents/agents/` |
| 7 | Supervisor + jira-story-breakdown implement plan → approve → route | 🔨 Build |
| 8 | Cross-repo subtasks gated on MERGE; supervisor resumable via Jira state | 🔨 Build supervisor + GitHub MCP |
| 9 | Live ops via MCP (static tool surface documented) | 🔨 Wire jira / github / pyspark-ops |
| 10 | Single CI quality gate on every PR | 🔨 `validate-skills.yml` |
| 11 | Consumption by reference; no per-repo copies | 🔨 Switch consumers |
| 12 | Semantic versioning + consumer-facing CHANGELOG; consumers pin | 🔨 Release policy |
| 13 | Least-privilege: agents scope `tools`; secrets via GSM | 🔨 Per agent |
| 14 | Evals for non-deterministic skills (jira-ticket-writer, write-genai-app) | 🔨 Add eval cases |
| 15 | Installable plugin + `llms.txt` + CONTRIBUTING + CHANGELOG | 🔨 Package & publish |

---

## Build & Migration Sequence (Priority Order)

| # | Step | Why first |
|---|------|-----------|
| 1 | Fix `templates/skill-template.md` to gold standard | Everything inherits it |
| 2 | Stand up CI gate: `test_skill_format.py` + `validate-skills.yml` | Catch defects before they spread |
| 3 | Apply v2 renames (five buckets, collision-safe names) | Naming is painful to change later |
| 4 | Fix `pipeline-builder` (4 known issues) + re-validate | Most complex config skill |
| 5 | Add eval cases for `jira-ticket-writer` | Non-deterministic — needs a ground truth |
| 6 | Build agent layer: 4 engineer agents + supervisor + `agent-template.agent.md` | Unlocks the picker + handoffs |
| 7 | Build `jira-story-breakdown` + `validate_plan.py` + `sizing-rubric.md` | Core of the new SDLC flow |
| 8 | Wire MCP: `jira-ops` + `github` into supervisor; `pyspark-ops` into app engineer | Makes supervisor resumable + cross-repo gates work |
| 9 | Migrate instructions into `instructions/<domain>/` | Consolidate from 3 source repos |
| 10 | Build 5 new `dag/` skills (real-execution-first method) | Don't generate cold from LLM |
| 11 | Switch consumers to reference mode; pin to tagged release | Retire per-repo copies |
| 12 | Package & tag `v1.0.0`, publish `plugin.json`, write first `CHANGELOG.md` | Portfolio artifact |

---

*Conforms to the open Agent Skills standard (agentskills.io) and the GitHub Copilot custom agents
format. Portable across Copilot (VS Code / CLI / cloud) · Claude Code · Cursor · Databricks Genie Code.*
