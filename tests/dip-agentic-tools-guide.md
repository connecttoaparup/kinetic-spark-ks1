# DIP Agentic Tools — Complete Platform & AI-SDLC Guide (v3)

The single source of truth for AI-assisted software development across all DIP ingestion work:
the PySpark ingestion app, ingestion YAML config, the Airflow plugin framework, and DAG JSON
config. This central repository (`dip-agentic-tools`) defines **instructions, principles, skills,
and agents** once, validates them in CI, and is **consumed by reference** from every repo and
developer machine.

Everything conforms to the open **Agent Skills** standard (agentskills.io, originated by
Anthropic) and the **GitHub Copilot custom agents** format, so the same artifacts work across
Copilot in VS Code, Copilot CLI, Copilot cloud agent, Claude Code, Cursor, and other
skills-compatible clients.

> **What changed in v3 (cross-repo execution):** subtasks can live in **different GitHub repos**
> (e.g. ingestion config in `progectai-ingestion`, DAG config in `progectai-dag`). v3 locks in the
> **sequential-PR-with-merge-gate** model (Option 1): a downstream subtask in a different repo is
> not dispatched until its upstream dependency's PR is **merged**. This adds a `repo` and
> `depends_on_merge` field to the plan, a **resumable orchestrator** that uses the **Jira story as
> the durable state store**, cross-repo merge-gate guardrails, and corrected walkthrough steps.
>
> **Carried from v2:** (1) five-bucket naming with collision-safe skill names; (2) renamed engineer
> agents + an orchestrator agent; (3) the `jira-story-breakdown` skill (read → assess → decompose →
> route); (4) **central-repo-by-reference** distribution (no per-repo sync workflow); (5) versioning
> & release policy; (6) full graphical AI-SDLC flow + step-by-step walkthrough with I/O.

---

## Table of contents

1. The mental model — four layers + reference consumption
2. Naming convention (the five buckets, rules, collision handling)
3. **Cross-repo execution model (Option 1: sequential PRs + merge gates)**
4. Complete directory structure
5. **The complete AI-SDLC graphical flow**
6. Sample files (all spec-accurate)
7. The execution plan: schema, validator, expected I/O
8. CI/CD — the quality gate
9. Consumption by reference (three mechanisms)
10. Versioning & release policy
11. **Step-by-step SDLC walkthrough (with expected inputs & outputs)**
12. Build & migration sequence
13. Maturity checklist

---

## 1. The mental model — four layers + reference consumption

There are exactly four customization layers. Maturity comes from putting each thing in the right
layer and never mixing them.

| Layer | Artifact | Loaded | Purpose |
|-------|----------|--------|---------|
| **Instructions** | `AGENTS.md`, `copilot-instructions.md` | Always, every turn | Stable, repo-wide standards every task needs |
| **Principles** | `.principles/**/*.md` | Referenced on demand | The *why*: architecture, domain context, anti-patterns, security |
| **Skills** | `SKILL.md` folders | Only when task matches description | The *how*: procedural, multi-step workflows with bundled scripts |
| **Agents** | `.agent.md` files | When selected or delegated | A persona that scopes tools and routes to the right skills/principles |
| **MCP** | server config in agents | When the agent calls a tool | Live operations: Jira fetch, job status, logs, trigger, cancel |

The fifth piece is **distribution**. In v2 this is **consumption by reference**: skills/agents
live once in `dip-agentic-tools`, are validated on every PR, are tagged into versioned releases,
and every consumer (developer or repo) **points back** to the central source rather than holding
copied files. No more per-repo `.github/skills/` copies, no more sync workflow, no more drift.

```
         dip-agentic-tools  (single source of truth — authored · validated · versioned)
                   │
   validate-skills.yml ◄────┤  (the ONLY quality gate — CI on every PR)
                   │
        tag release v1.x ───┤  (immutable, changelog-backed)
                   │
                   ▼  consumed BY REFERENCE (no copies pushed downstream)
        ┌──────────┴──────────┬─────────────────────┐
   gh skill install      chat.agentFilesLocations    plugin install
   (→ ~/.copilot/skills,  (→ points at central        (whole bundle from
    provenance-pinned)     clone for agents)           plugin.json)
```

### How an agent actually "calls" a skill

You do **not** replace skills with agents — you nest skills under an agent:

1. You select an agent (e.g. `dip-ings-app-config-engineer`) from the VS Code agent picker, or
   run `copilot --agent dip-ings-app-config-engineer` in the CLI.
2. The agent's body and `tools` array scope what it can touch.
3. When your prompt matches a skill's `description`, that `SKILL.md` is injected into context
   (progressive disclosure stage 2).
4. The agent follows the skill, optionally running its bundled scripts (stage 3).

> **Invocation reality check.** In **VS Code**, custom agents are chosen from the *agent picker
> dropdown* — `@name` is reserved for built-in chat participants (`@workspace`, `@terminal`), not
> custom agents. In **Copilot CLI**, use `/agent` interactively or `--agent <name>` as a flag. In
> both surfaces, Copilot can also auto-delegate to your agent as a **subagent** with its own
> context window. Skills are force-loaded with `/skill-name`; otherwise they auto-activate by
> description match.

---

## 2. Naming convention

### The principle

**The folder path carries the domain; the skill name carries the action.** Don't repeat the
domain prefix inside an already-domain-scoped folder — it's noise. Skill leaf names are
`<action>-<object>`, lowercase-hyphen, and the `name` field **must equal the parent directory
name** (a hard spec rule). The team prefix `dip-ings-` lives only on user-facing entities: the
repo root, the agents (which you pick from a dropdown across many repos), and the plugin.

### The five domain buckets

| # | Folder | Covers | Old name |
|---|--------|--------|----------|
| 1 | `common/` | Cross-cutting; applies to all repos | `dip-ings/` |
| 2 | `app/` | PySpark ingestion app code | `dip_ings_app_core/` |
| 3 | `app-config/` | Ingestion YAML config | `dip_ings_app_config/` |
| 4 | `dag/` | Airflow plugin framework code | `dip_ings_dag_core/` |
| 5 | `dag-config/` | DAG JSON config | `dip_ings_dag_config/` |

Folders use hyphens too (not the old `_core` underscores) so folder names and skill names share
one style. `app`/`app-config` and `dag`/`dag-config` express the framework-vs-config contrast
more cleanly than `*_core`/`*_config` did.

### Collision rule (critical for `gh skill install`)

When a skill is installed personally it lands flat in `~/.copilot/skills/<name>/`, so the **`name`
must be globally unique** across all skills — the folder path no longer disambiguates. Rule:
**the primary domain keeps the clean name; the one that would collide gets a domain qualifier.**

Applied collisions:

| Concept | Primary (clean name) | Secondary (qualified) |
|---------|----------------------|-----------------------|
| validate config | `validate-app-config` (app-config) | `validate-dag-config` (dag-config) |
| write a service | `write-service` (app, PySpark) | `write-airflow-service` (dag) |
| review a PR | `review-pr` (common, one shared skill) | — (don't duplicate; common handles all) |
| onboard | `onboard-source` (app-config) | `onboard-dag` (dag-config) |

---

## 3. Cross-repo execution model (Option 1: sequential PRs + merge gates)

The DIP domains do **not** all live in one repo. Ingestion config lives in `progectai-ingestion`,
DAG config in `progectai-dag`, the PySpark app in `pyspark-ingestion-app`, the Airflow plugin
framework in `composer`. So when a single Jira story spans domains, its subtasks land in
**different repos with different working trees, CODEOWNERS, and CI** — the orchestrator cannot
treat them as one filesystem.

### The decision: Option 1

We sequence cross-repo subtasks: **a subtask in a different repo is dispatched only after its
upstream dependency's PR is merged.** This is not a workaround — it expresses the true
dependency. A DAG that schedules a job must not be authored until that job actually exists and is
merged; otherwise you ship a broken DAG referencing a non-existent job.

Why Option 1 over a shared registry (Option 2):

- **Matches the org.** Separate repos exist because the domains have different reviewers, risk
  profiles, and release cadences. A shared registry adds a third artifact everyone must learn
  before anything ships.
- **Correct by design.** The merge gate enforces "config exists before the DAG that uses it."
- **Auditable.** Each subtask is its own reviewed PR, linked to the story.
- **Right-sized.** The registry (Option 2) solves a throughput problem you don't have yet — many
  parallel cross-repo stories. Revisit it only when sequential merge gates become a real
  bottleneck; until then it's premature complexity.

### What Option 1 requires

**1. A `repo` field on every subtask** — so the orchestrator knows which working tree each
subtask belongs to, and can detect when a dependency crosses a repo boundary.

**2. A merge gate for cross-repo dependencies** — `depends_on_merge: true` is set automatically
whenever a subtask depends on another subtask in a *different* repo. Same-repo dependencies don't
need it (they can even share a PR).

**3. A resumable orchestrator backed by the Jira story.** PR reviews take hours or days; the CLI
session that planned the work will be long dead by the time the upstream PR merges. So the
orchestrator must be **stateless between runs** and treat the **Jira story as the durable state
store**. It writes each subtask's status and PR URL back to the story via
`jira-ops/update_issue`, and on resume it reads the story to decide what to dispatch next.

```
Jira story DIP-1234  (the single source of truth for run state)
├── DIP-1234-1  repo: progectai-ingestion   status: merged   PR: progectai-ingestion#101
├── DIP-1234-2  repo: progectai-ingestion   status: merged   PR: progectai-ingestion#102
└── DIP-1234-3  repo: progectai-dag         status: pending  (deps merged → ready to dispatch)
```

When the developer returns the next day and says "continue DIP-1234", the orchestrator reads the
story, sees 1 and 2 are merged, and dispatches 3 — no rework, no lost context.

### Repo ↔ domain map

| Domain | Repo | Owner agent |
|--------|------|-------------|
| `app` | `pyspark-ingestion-app` | `dip-ings-app-engineer` |
| `app-config` | `progectai-ingestion` | `dip-ings-app-config-engineer` |
| `dag` | `composer` | `dip-ings-dag-engineer` |
| `dag-config` | `progectai-dag` | `dip-ings-dag-config-engineer` |

### Dispatch rule (the heart of Option 1)

```
For each subtask S in dependency order:
  if every dep of S is in the SAME repo as S:
      dispatch S as soon as deps are locally done   (may even share a PR)
  else (S has a dep in a DIFFERENT repo):
      wait until that dep's PR status == merged      (read from Jira story state)
      only then dispatch S
  after S's PR opens: write {status, PR url} back to the Jira story
```

This needs a GitHub MCP (or `gh` via an MCP/tool) to read PR merge status. The orchestrator polls
it on resume; it does not block a live session waiting for a human to merge.

---

## 4. Complete directory structure

```
dip-agentic-tools/                          # team prefix lives HERE, once
│
├── .agents/
│   ├── AGENTS.md                            # Master config (always-on)
│   │
│   ├── agents/                              # The persona layer (.agent.md files)
│   │   ├── dip-ings-orchestrator.agent.md   # Entry point: reads plan, routes subtasks
│   │   ├── dip-ings-app-engineer.agent.md
│   │   ├── dip-ings-app-config-engineer.agent.md
│   │   ├── dip-ings-dag-engineer.agent.md
│   │   └── dip-ings-dag-config-engineer.agent.md
│   │
│   └── skills/
│       ├── common/                          # All repos
│       │   ├── jira-story-breakdown/        # NEW — read · assess · decompose · route
│       │   ├── jira-ticket-writer/          # writes tickets (needs evals)
│       │   ├── review-pr/
│       │   ├── generate-docs/
│       │   ├── debug-pipeline/
│       │   └── devops-infra-tickets/
│       │
│       ├── app/                             # PySpark ingestion app
│       │   ├── write-task/
│       │   ├── write-service/
│       │   ├── write-unit-test/
│       │   ├── write-genai-app/
│       │   ├── tsql-to-bq/
│       │   ├── barricade-migrate/
│       │   └── validate-yaml-config/
│       │
│       ├── app-config/                      # Ingestion YAML config
│       │   ├── pipeline-builder/            # was etl-pipeline-builder (needs 4 fixes)
│       │   ├── add-environment/
│       │   ├── add-job/
│       │   ├── add-pipeline/
│       │   ├── add-sql/
│       │   ├── onboard-source/
│       │   └── validate-app-config/
│       │
│       ├── dag/                             # Airflow plugin framework (5 NEW)
│       │   ├── write-operator/
│       │   ├── write-sensor/
│       │   ├── write-airflow-service/
│       │   ├── write-generator/
│       │   └── debug-plugin/
│       │
│       └── dag-config/                      # DAG JSON config
│           ├── add-dag/
│           ├── add-task/
│           ├── add-template/
│           ├── debug-dag-config/
│           ├── onboard-dag/
│           ├── upgrade-plugin/
│           └── validate-dag-config/
│
├── .principles/
│   ├── principles.md                        # Platform-wide values
│   ├── architecture.md                      # DIP Ingestion architecture overview
│   ├── security.md                          # GSM, PII, least-privilege (all repos)
│   ├── app/
│   │   ├── architecture.md
│   │   ├── domain-context.md
│   │   ├── patterns.md
│   │   ├── anti-patterns.md
│   │   ├── code-style.md
│   │   └── testing.md
│   ├── app-config/
│   │   ├── architecture.md
│   │   ├── domain-context.md
│   │   └── anti-patterns.md
│   ├── dag/
│   │   ├── architecture.md
│   │   ├── domain-context.md
│   │   └── security.md
│   └── dag-config/
│       ├── architecture.md
│       └── domain-context.md
│
├── instructions/
│   ├── app/            { copilot-instructions.md, instructions/ }   # migrate: pyspark .github
│   ├── app-config/     { copilot-instructions.md, instructions/ }   # NEW (none today)
│   ├── dag/            { copilot-instructions.md, instructions/ }   # migrate: composer .github (11 files)
│   └── dag-config/     { copilot-instructions.md, instructions/ }   # migrate: progectai-dag .github
│
├── profiles/                                # Human-readable role docs (source for agents/)
│   ├── app-engineer.md
│   ├── app-config-engineer.md
│   ├── dag-engineer.md
│   └── dag-config-engineer.md
│
├── templates/
│   ├── skill-template.md                    # Gold standard (fix FIRST)
│   ├── agent-template.agent.md
│   ├── copilot-instructions-template.md
│   └── principles-template.md
│
├── tests/
│   └── test_skill_format.py                 # CI quality gate
│
├── .github/
│   └── workflows/
│       └── validate-skills.yml              # The ONLY workflow — runs on every PR
│
├── docs/
│   └── agentic-sdlc-flow.md
├── plugin.json                              # Installable bundle (agents + skills)
├── llms.txt
├── CONTRIBUTING.md
└── CHANGELOG.md
```

> **Note:** there is no `sync-skills.yml` and no `eng/sync.sh` in v2. Distribution is by
> reference (§8), not by pushing copies.

---

## 5. The complete AI-SDLC graphical flow

This is the full journey from a Jira story to a merged PR, showing every layer, every gate, and
who does what. The golden rule is visible in it: **the Jira skill plans; the agents build.**

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                            DIP AGENTIC AI-SDLC  (end to end)                            │
└──────────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐
  │  Jira story │   e.g. DIP-1234 "Onboard CRM customers+orders to BQ with daily DAG"
  │  (DIP-1234) │
  └──────┬──────┘
         │  developer: "start work on DIP-1234"
         ▼
  ╔═══════════════════════════════════════════════════════════════════════════╗
  ║  AGENT: dip-ings-orchestrator           (always-on: AGENTS.md, instructions)║
  ╚═══════════════════════════════════════════════════════════════════════════╝
         │  activates skill by description match
         ▼
  ┌────────────────────────────────────────────────────────────────────────────┐
  │  SKILL: common/jira-story-breakdown                                         │
  │  ───────────────────────────────────────────────────────────────────────── │
  │  1. READ      ── jira-ops MCP → get_issue(DIP-1234)                         │
  │  2. ASSESS    ── size + domain spread  (references/sizing-rubric.md)        │
  │  3. DECOMPOSE ── split into domain-scoped subtasks w/ depends_on            │
  │  4. ROUTE     ── tag each subtask with owner_agent                          │
  │  5. EMIT      ── write /tmp/DIP-1234-plan.json                              │
  │  6. VALIDATE  ── scripts/validate_plan.py  (domains real? deps acyclic?)    │
  │  ── OUTPUT: execution plan (JSON). NO CODE WRITTEN. ──                      │
  └───────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ▼
                        ╔══════════════════╗
                        ║  HUMAN GATE 🧑    ║   developer reviews & approves the plan
                        ║  approve plan?   ║   (edit / reject / approve)
                        ╚════════┬═════════╝
                                 │ approved
                                 ▼
  ╔═══════════════════════════════════════════════════════════════════════════╗
  ║  AGENT: dip-ings-orchestrator  (RESUMABLE — state lives in the Jira story)  ║
  ║  reads plan, dispatches in depends_on order, honoring CROSS-REPO merge gates║
  ╚═══════════════════════════════════════════════════════════════════════════╝
         │                         │                          │
         │ subtask 1               │ subtask 2 (after 1,      │ subtask 3 (after 1&2 MERGED,
         │ repo: progectai-ingestion │ same repo)               │ repo: progectai-dag → CROSS-REPO)
         ▼                         ▼                          ▼
  ┌──────────────┐         ┌──────────────┐          ┌──────────────────┐
  │ HANDOFF →    │         │ HANDOFF →    │          │  ⛔ MERGE GATE     │
  │ app-config-  │         │ app-config-  │          │  wait: PRs for    │
  │ engineer     │         │ engineer     │          │  1 & 2 == merged  │
  │ (subagent)   │         │ (subagent)   │          │  (read from Jira) │
  └──────┬───────┘         └──────┬───────┘          └────────┬─────────┘
         │ skill: add-job         │ skill: add-sql            │ gate passed →
         ▼                        ▼                           ▼ HANDOFF → dag-config-engineer
  plan→validate→execute    plan→validate→execute       plan→validate→execute
  writes customers.yaml,   writes orders_enrich.sql    writes daily_crm_dag.json
  orders.yaml                                          (references MERGED job names)
         │                        │                           │
         ▼                        ▼                           ▼
  PR progectai-ingestion#101  PR progectai-ingestion#102    PR progectai-dag#201
  validate-app-config       validate-app-config         validate-dag-config
         │                        │                           │
         └─ status→Jira ──────────┴─ status→Jira ─────────────┴─ status→Jira
            (orchestrator writes {status, PR url} back to DIP-1234 after each PR opens)
                                  │
        ⏳ each PR: HUMAN REVIEW + MERGE (per-repo CODEOWNERS & CI)  🧑
                                  ▼
  ┌────────────────────────────────────────────────────────────────────────────┐
  │  On resume ("continue DIP-1234"): orchestrator re-reads the Jira story,      │
  │  sees which subtasks are merged, and dispatches only what's now unblocked.   │
  └───────────────────────────────┬────────────────────────────────────────────┘
                                  ▼
  ┌────────────────────────────────────────────────────────────────────────────┐
  │  SKILL: common/review-pr     → drafts each PR body vs pull_request_template  │
  │  SKILL: common/jira-ticket-writer → keeps DIP-1234 subtask status current    │
  └───────────────────────────────┬────────────────────────────────────────────┘
                                  ▼
                            ┌───────────┐
                            │ ALL MERGED│
                            │    ✅      │
                            └───────────┘

  ── Skills/agents come from dip-agentic-tools BY REFERENCE, validated by
     validate-skills.yml and pinned to a released version (§9, §10). ──
  ── Golden rule: the Jira skill PLANS; the agents BUILD; cross-repo deps wait for MERGE. ──
```

---

## 6. Sample files (all spec-accurate)

### 6.1 `.agents/AGENTS.md` — master, always-on

Keep it short; it's injected every turn.

```markdown
# DIP Agentic Tools

Governs AI-assisted development across all DIP ingestion repos.

## Stack (non-negotiable)
- Compute: PySpark 3.5 on Dataproc. Orchestration: Cloud Composer (Airflow 2.x). Sink: BigQuery.
- Language: Python 3.9+. Never propose pandas for large-data transforms — use PySpark.

## Organization
- `.principles/` — read for the "why" before non-trivial work.
- `.agents/skills/` — task workflows; they activate automatically by description.
- `.agents/agents/` — personas; select the one matching the task, or start with the orchestrator.

## Hard rules
- Never hardcode GCP project IDs — always `${GCP_PROJECT}`.
- All secrets via GSM; never inline credentials (`.principles/security.md`).
- Every config or code change must pass its domain validator before being called done.

## Routing
- Jira story to start? → dip-ings-orchestrator (it plans, then routes).
- PySpark app code → dip-ings-app-engineer
- Ingestion YAML config → dip-ings-app-config-engineer
- Airflow plugin framework → dip-ings-dag-engineer
- DAG JSON config → dip-ings-dag-config-engineer
```

---

### 6.2 `.principles/app-config/anti-patterns.md` — highest-value principle file

```markdown
# Ingestion Config — Anti-Patterns

## ❌ Two-part BigQuery table references
`target_bq_table: dataset.table` passes eyeballing but fails silently at runtime.
✅ Always three-part: `${GCP_PROJECT}.dataset.table`.

## ❌ Quoting the project placeholder
The runner resolves `${GCP_PROJECT}` only when unquoted. Quoting ships the literal string.

## ❌ Incremental load without a watermark
`load_mode: incremental` with no `watermark_col` reloads everything every run.
✅ incremental and cdc both require `watermark_col`.

## ❌ Reusing a job name across pipelines
Job names are globally unique in the registry; collisions overwrite scheduling state.

## ❌ partition_col on a CDC job
CDC ignores it and warns. Omit it.
```

---

### 6.3 `instructions/app-config/copilot-instructions.md` — per-domain, always-on

```markdown
# Ingestion Config Repo — Copilot Instructions

You are working in an DIP ingestion **config** repo. Assets are YAML config files (sources,
jobs, pipelines, SQL). You are NOT editing PySpark app code here.

## On every task
1. Match the request to a skill in the central skills (they auto-activate).
2. Before declaring done, run `validate-app-config`.
3. Reference `.principles/app-config/` for domain context and anti-patterns.

## Conventions
- One job per file: `configs/jobs/<source>/<job_name>.yaml`.
- Pipelines compose jobs by reference, never duplication.
- PRs touching config require the `pull_request_template.md` checklist completed.
```

---

### 6.4 Gold-standard skill — `app-config/add-job/SKILL.md`

> **Input:** source, job_name, target table, load_mode, (watermark/partition cols).
> **Output:** a validated job YAML at `configs/jobs/<source>/<job_name>.yaml`.

```markdown
---
name: add-job
description: >
  Add a new ingestion job to the DIP ingestion YAML config. Use when onboarding a new
  table/source, creating a job definition, or when the user says "add a job", "ingest a
  new table", or configure full/incremental/cdc loading. Produces a validated job YAML.
license: Proprietary. See LICENSE.txt
compatibility: Requires Python 3.9+ and the dip_ings_config package (validator).
metadata:
  domain: app-config
  owner: dip-platform
  version: "1.2"
---

# Add an Ingestion Job

Create a job YAML at `configs/jobs/<source>/<job_name>.yaml`.

## Workflow (plan → validate → execute)
1. **Gather** required fields. If any missing, ask before writing:
   | Field | Values | Notes |
   |-------|--------|-------|
   | `source` | string | Must exist in `references/source-registry.md` (case-sensitive) |
   | `job_name` | string | Globally unique; verify against registry |
   | `target_bq_table` | `${GCP_PROJECT}.dataset.table` | Three-part, unquoted |
   | `load_mode` | full \| incremental \| cdc | See rules below |
   | `watermark_col` | string | Required for incremental and cdc |
   | `partition_col` | string | Omit for cdc |
2. **Plan**: write YAML to `/tmp/<job_name>.yaml`. Do not touch `configs/` yet.
3. **Validate**: `python scripts/validate_job.py /tmp/<job_name>.yaml`. Loop until it passes.
4. **Execute**: move the validated file to `configs/jobs/<source>/<job_name>.yaml`.
5. **Confirm**: run the `validate-app-config` skill for cross-file collisions.

## Load-mode rules
- `full`: truncate + reload. No `watermark_col`.
- `incremental`: append where `watermark_col > last_run`. Requires `watermark_col`.
- `cdc`: requires `configs/cdc/<job_name>.json`. Omit `partition_col`.

## Gotchas
- `target_bq_table` two-part form fails at runtime, not validation. Always three-part.
- Do not quote `${GCP_PROJECT}`.
- Job names collide globally — check `references/source-registry.md` first.
- `source` is case-sensitive.

## Reference
Read [job-schema](references/job-schema.md) only if validation reports an unknown field.
See [assets/incremental-job.yaml](assets/incremental-job.yaml) for a canonical example.
```

**Folder layout**
```
add-job/
├── SKILL.md
├── scripts/validate_job.py
├── references/{job-schema.md, source-registry.md}
└── assets/incremental-job.yaml
```

---

### 6.5 The orchestration skill — `common/jira-story-breakdown/SKILL.md`

This is the new capability management asked for. It **reads, assesses, decomposes, and routes** —
and explicitly never writes code.

> **Input:** a Jira story ID (e.g. `DIP-1234`).
> **Output:** a validated execution plan at `/tmp/<story>-plan.json` (schema in §7). No code.

```markdown
---
name: jira-story-breakdown
description: >
  Read a Jira story, assess its size and domain spread, and produce a structured execution
  plan that routes subtasks to the right DIP engineer agents. Use when starting work from a
  Jira story/ticket, or when asked to "break down", "plan", or "scope" a story. Produces a
  plan only — it does NOT write application code.
license: Proprietary. See LICENSE.txt
compatibility: Requires the Jira MCP server (jira-ops) configured.
metadata:
  domain: common
  owner: dip-platform
  version: "0.1"
---

# Jira Story Breakdown & Routing

You produce an execution PLAN. You never write application code. After the plan is approved,
the orchestrator agent dispatches subtasks to engineer agents that do the building.

## Workflow
1. **Read**: fetch the story via `jira-ops/get_issue`. If only an ID is given, fetch it — never
   work from pasted text when the ID is available.
2. **Assess**: score size and domain spread against `references/sizing-rubric.md`.
3. **Decide**:
   - small + single-domain → a one-subtask plan (no decomposition theatre).
   - large OR multi-domain → decompose into domain-scoped subtasks with `depends_on`.
4. **Route**: tag every subtask with its `domain` and `owner_agent` (table below).
5. **Emit**: write the plan to `/tmp/<story>-plan.json` in the schema in `references/plan-schema.md`.
6. **Validate**: `python scripts/validate_plan.py /tmp/<story>-plan.json`
   (every domain/owner_agent real? dependencies acyclic? each subtask exactly one domain?).
7. **Present and STOP**: show the plan and wait for human approval. Do not hand off yourself.

## Routing table
| Domain | owner_agent |
|--------|-------------|
| app          | dip-ings-app-engineer |
| app-config   | dip-ings-app-config-engineer |
| dag          | dip-ings-dag-engineer |
| dag-config   | dip-ings-dag-config-engineer |

## Sizing rubric (summary; full detail in references/sizing-rubric.md)
Treat as "large / needs decomposition" if ANY of:
- spans more than one domain, OR
- > 5 acceptance criteria, OR
- estimated > 8 story points, OR
- touches > 1 source system or > 3 config files.

## Gotchas
- Do NOT write code, even for a trivial story. Emit the plan; the agents build.
- A subtask must belong to exactly one domain. If it spans two, split it.
- If scope is ambiguous, ask ONE clarifying question before decomposing — don't guess.
- Set `depends_on` so config exists before the DAG that schedules it.
```

**Folder layout**
```
jira-story-breakdown/
├── SKILL.md
├── scripts/validate_plan.py
└── references/{plan-schema.md, sizing-rubric.md}
```

---

### 6.6 `templates/skill-template.md` — fix this FIRST

```markdown
---
name: REPLACE-with-name-matching-directory
description: >
  REPLACE. What the skill does AND when to use it, including trigger words a user would type.
  Max 1024 chars.
license: Proprietary. See LICENSE.txt
compatibility: REPLACE or DELETE if no special environment is needed.
metadata:
  domain: REPLACE   # common | app | app-config | dag | dag-config
  owner: dip-platform
  version: "0.1"
---

# <Human Title>

<One line on the outcome this skill produces.>

## Workflow
1. Gather inputs (ask if missing — list required fields in a table).
2. Plan to a temp location.
3. Validate with a bundled script; loop until it passes.
4. Execute (write to the real location).
5. Confirm with the domain validator.

## Rules
<Prescriptive for fragile ops. ONE default; mention alternatives in a line.>

## Gotchas
- <Concrete correction to a mistake the agent makes without being told.>
- <Add a bullet every time you correct the agent in real use.>

## Reference
Read [references/REFERENCE.md](references/REFERENCE.md) only when <specific trigger>.
```

Calibration baked in: *add what the agent lacks, omit what it knows*; *procedures over
declarations*; *defaults, not menus*; *gotchas are the payload*.

---

### 6.7 Engineer agent — `.agents/agents/dip-ings-app-config-engineer.agent.md`

> **Input:** a config task (a subtask handed from the orchestrator, or a direct prompt).
> **Output:** validated YAML config + a finished domain validation pass.

```markdown
---
name: dip-ings-app-config-engineer
description: >
  DIP ingestion config engineer. Authors, validates, and reviews ingestion YAML config —
  jobs, pipelines, SQL, environments — and onboards sources. Use for ingestion config work
  (not PySpark app code, not DAG JSON).
tools: ['read', 'edit', 'search', 'execute']
model: Claude Opus 4.5
handoffs:
  - label: Wire the DAG for this config
    agent: dip-ings-dag-config-engineer
    prompt: Create/extend the DAG JSON config that schedules the job(s) just added.
    send: false
---

# DIP Ingestion Config Engineer

You own the ingestion **config** surface. You write YAML, not PySpark.

## Operating rules
- Read `.principles/app-config/{domain-context,anti-patterns}.md` before non-trivial changes.
- Route by task:
  - "add a job / onboard a table" → add-job
  - "new pipeline" → add-pipeline
  - "add SQL" → add-sql
  - "new environment" → add-environment
  - "onboard a source end-to-end" → onboard-source
  - any change → finish with validate-app-config
- Cross-cutting: review-pr, generate-docs, devops-infra-tickets.

## Guardrails
- Never edit `configs/` directly without validating a temp copy first.
- Never hardcode project IDs or secrets.
- When config implies scheduling, hand off to dag-config-engineer — don't author DAG JSON.
```

---

### 6.8 Orchestrator agent — `.agents/agents/dip-ings-orchestrator.agent.md`

> **Input:** a Jira story ID, or a resume request on an in-flight story.
> **Output:** dispatched subtasks (handoffs) in dependency order, with cross-repo merge gates
> respected and status written back to the Jira story.

```markdown
---
name: dip-ings-orchestrator
description: >
  Entry-point coordinator for DIP ingestion work that starts from a Jira story. Breaks the
  story down via the jira-story-breakdown skill, then routes each subtask to the right
  engineer agent in dependency order across repos. Resumable: keeps run state in the Jira
  story. Does not write code itself.
tools: ['read', 'search', 'jira-ops/get_issue', 'jira-ops/update_issue', 'github/get_pull_request']
model: Claude Opus 4.5
mcp-servers:
  jira-ops:
    type: http
    url: https://jira-ops-xxxx.run.app/sse
    env:
      MCP_TOKEN: ${{ secrets.COPILOT_MCP_JIRA_TOKEN }}
  github:
    type: http
    url: https://github-mcp-xxxx.run.app/sse
    env:
      MCP_TOKEN: ${{ secrets.COPILOT_MCP_GITHUB_TOKEN }}
handoffs:
  - label: Build app subtask
    agent: dip-ings-app-engineer
    send: false
  - label: Build app-config subtask
    agent: dip-ings-app-config-engineer
    send: false
  - label: Build dag subtask
    agent: dip-ings-dag-engineer
    send: false
  - label: Build dag-config subtask
    agent: dip-ings-dag-config-engineer
    send: false
---

# DIP Ingestion Orchestrator

You coordinate; you do not build. You are RESUMABLE: the Jira story is your state store.

## On a NEW story
1. Activate `jira-story-breakdown` → `/tmp/<story>-plan.json`.
2. Present the plan and WAIT for human approval. Never skip this gate.
3. On approval, write each subtask (id, repo, domain, owner_agent, depends_on, status=pending)
   back to the Jira story via `jira-ops/update_issue`. The story is now the source of truth.

## On RESUME ("continue DIP-1234")
1. Read current state via `jira-ops/get_issue`. Do NOT re-plan.
2. For each subtask still `pending`, check whether it is dispatchable (rule below).

## Dispatch rule (cross-repo aware)
For a subtask S in dependency order:
- If every `depends_on` of S is in the SAME `repo` as S → dispatchable once those deps are done
  locally (they may even share a PR).
- If any `depends_on` of S is in a DIFFERENT `repo` (`depends_on_merge: true`) → S is dispatchable
  ONLY when each cross-repo dependency's PR status is `merged`. Read PR status via
  `github/get_pull_request` using the PR url stored on the dependency's subtask in the story.
- Never dispatch a subtask whose dependencies are unmet or unmerged.

## After dispatching
- When the engineer agent opens a PR, record `{status: in_review, pr_url}` on that subtask in the
  Jira story. When CI/merge state changes, update to `merged`.
- After ALL subtasks are `merged`, trigger `review-pr` summary and set the story Done.

## Guardrails
- Do not write application code. If tempted, hand off.
- Do not block a live session waiting for a human to merge — record state and stop; the human
  resumes you later.
- If an engineer agent reports a blocker, pause and surface it to the human.
```

---

### 6.9 MCP wiring — Jira + PySpark ops

Live operations belong in MCP, not skills. Each server, two transports (local stdio for dev;
HTTP/SSE on Cloud Run for remote + Atlassian Rovo).

```yaml
# inside an agent's frontmatter
mcp-servers:
  jira-ops:
    type: http
    url: https://jira-ops-xxxx.run.app/sse
    env:
      MCP_TOKEN: ${{ secrets.COPILOT_MCP_JIRA_TOKEN }}
  github:                            # orchestrator: read PR merge status for cross-repo gates
    type: http
    url: https://github-mcp-xxxx.run.app/sse
    env:
      MCP_TOKEN: ${{ secrets.COPILOT_MCP_GITHUB_TOKEN }}
  pyspark-ops:                       # local dev transport
    type: local
    command: python
    args: ['-m', 'pyspark_mcp.server']
    tools: ['*']
    env:
      MCP_ENV: dev
```

The `github` server is what makes Option 1 automatable: the orchestrator calls
`github/get_pull_request` to confirm a cross-repo dependency's PR is `merged` before dispatching
the dependent subtask.

> Architectural note for `debug-pipeline`: the MCP tool surface is **static, defined at the
> server's build time** — it does not discover Dataproc jobs at runtime. Document the fixed tool
> list in the skill so the agent doesn't hallucinate tools.

---

### 6.10 `plugin.json` — installable bundle (the portfolio artifact)

```json
{
  "name": "dip-ings-platform",
  "version": "1.0.0",
  "description": "DIP ingestion agentic SDLC: orchestrator + engineer agents and skills for PySpark + Airflow ingestion, config, and DAGs.",
  "agents": [".agents/agents"],
  "skills": [".agents/skills"],
  "commands": []
}
```

### 6.11 `llms.txt`

```
# DIP Agentic Tools

## Docs
- [Agentic SDLC flow](docs/agentic-sdlc-flow.md): how a developer uses agents+skills day to day.
- [Architecture](.principles/architecture.md): DIP ingestion platform overview.
- [Security](.principles/security.md): GSM, PII, least-privilege.
- [Contributing](CONTRIBUTING.md): how to add or change a skill/agent (with the CI gate).
```

---

## 7. The execution plan: schema, validator, expected I/O

### 7.1 Plan schema (`references/plan-schema.md`)

> **Produced by:** `jira-story-breakdown`. **Consumed by:** `dip-ings-orchestrator`.
> Note the `repo` and `depends_on_merge` fields that drive cross-repo gating (§3).

```json
{
  "story": "DIP-1234",
  "title": "Onboard CRM customers + orders into BQ with daily DAG",
  "assessment": {
    "size": "large",
    "spans_domains": true,
    "spans_repos": true,
    "rationale": "Two tables + a SQL transform in progectai-ingestion; DAG scheduling in progectai-dag."
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

Field notes:
- `repo`: which GitHub repo this subtask is built in (drives working-tree routing).
- `depends_on_merge`: set `true` automatically when any `depends_on` subtask is in a *different*
  `repo`. The orchestrator then waits for that dependency's PR to be `merged` before dispatching.
- `status` / `pr_url`: the live run state the orchestrator writes back to the Jira story, making
  the run resumable.

### 7.2 Plan validator (`scripts/validate_plan.py`)

> **Input:** a plan JSON path. **Output:** exit 0 + "OK" on success; exit 1 + error list on
> failure (so the skill can loop and self-correct). Also auto-derives `depends_on_merge` from
> cross-repo dependencies and flags mismatches.

```python
"""Validate a jira-story-breakdown execution plan before any handoff."""
import json
import sys

VALID_DOMAINS = {"common", "app", "app-config", "dag", "dag-config"}
DOMAIN_TO_AGENT = {
    "app": "dip-ings-app-engineer",
    "app-config": "dip-ings-app-config-engineer",
    "dag": "dip-ings-dag-engineer",
    "dag-config": "dip-ings-dag-config-engineer",
}
DOMAIN_TO_REPO = {
    "app": "pyspark-ingestion-app",
    "app-config": "progectai-ingestion",
    "dag": "composer",
    "dag-config": "progectai-dag",
}


def validate(path: str) -> list[str]:
    errs: list[str] = []
    plan = json.loads(open(path, encoding="utf-8").read())

    if not plan.get("story"):
        errs.append("missing 'story'")
    subtasks = plan.get("subtasks", [])
    if not subtasks:
        errs.append("plan has no subtasks")

    by_id = {s.get("id"): s for s in subtasks}
    ids = set(by_id)

    for s in subtasks:
        sid = s.get("id", "<no id>")
        dom = s.get("domain")
        repo = s.get("repo")

        if dom not in VALID_DOMAINS:
            errs.append(f"{sid}: invalid domain '{dom}'")
        else:
            if dom in DOMAIN_TO_AGENT and s.get("owner_agent") != DOMAIN_TO_AGENT[dom]:
                errs.append(f"{sid}: owner_agent should be '{DOMAIN_TO_AGENT[dom]}' for '{dom}'")
            if dom in DOMAIN_TO_REPO and repo != DOMAIN_TO_REPO[dom]:
                errs.append(f"{sid}: repo should be '{DOMAIN_TO_REPO[dom]}' for domain '{dom}'")

        # cross-repo dependency → depends_on_merge MUST be true
        cross = False
        for dep in s.get("depends_on", []):
            if dep not in ids:
                errs.append(f"{sid}: depends_on unknown subtask '{dep}'")
                continue
            if by_id[dep].get("repo") != repo:
                cross = True
        if cross and not s.get("depends_on_merge"):
            errs.append(f"{sid}: has a cross-repo dependency → depends_on_merge must be true")
        if not cross and s.get("depends_on_merge"):
            errs.append(f"{sid}: depends_on_merge is true but no dependency crosses a repo")

    # cycle detection (Kahn's algorithm)
    indeg = {s["id"]: 0 for s in subtasks}
    adj: dict[str, list[str]] = {s["id"]: [] for s in subtasks}
    for s in subtasks:
        for dep in s.get("depends_on", []):
            if dep in adj:
                adj[dep].append(s["id"])
                indeg[s["id"]] += 1
    queue = [n for n, d in indeg.items() if d == 0]
    seen = 0
    while queue:
        n = queue.pop()
        seen += 1
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    if seen != len(subtasks):
        errs.append("dependency cycle detected — subtasks cannot be ordered")

    return errs


if __name__ == "__main__":
    errors = validate(sys.argv[1])
    if errors:
        print("PLAN INVALID:\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)
    print("OK: plan is valid, acyclic, and cross-repo gates are correct.")
```

---

## 8. CI/CD — the quality gate

With distribution by reference, the central CI gate is the **only** safety net — there's no
downstream PR review to catch a bad skill. So it matters more, not less.

### 7.1 `tests/test_skill_format.py`

```python
"""Validate every SKILL.md against the Agent Skills spec. Fails CI on any violation."""
import re, sys, yaml
from pathlib import Path

SKILLS_ROOT = Path(".agents/skills")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME, MAX_DESC, MAX_LINES = 64, 1024, 500


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        raise ValueError("missing YAML frontmatter")
    _, fm, _ = text.split("---", 2)
    return yaml.safe_load(fm) or {}


def check(md: Path) -> list[str]:
    e, text, d = [], md.read_text(encoding="utf-8"), md.parent.name
    try:
        fm = parse_frontmatter(text)
    except Exception as ex:  # noqa: BLE001
        return [f"{md}: {ex}"]
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not name: e.append(f"{md}: missing name")
    else:
        if len(name) > MAX_NAME: e.append(f"{md}: name >{MAX_NAME}")
        if not NAME_RE.match(name): e.append(f"{md}: name must be lowercase/hyphens, no leading/trailing/double hyphen")
        if name != d: e.append(f"{md}: name '{name}' != dir '{d}'")
    if not desc: e.append(f"{md}: missing description")
    elif len(desc) > MAX_DESC: e.append(f"{md}: description >{MAX_DESC}")
    if text.count("\n") > MAX_LINES: e.append(f"{md}: >{MAX_LINES} lines — move detail to references/")
    return e


def main() -> int:
    skills = list(SKILLS_ROOT.rglob("SKILL.md"))
    if not skills:
        print("No SKILL.md found."); return 1
    # global uniqueness of names (flat-install collision guard)
    names: dict[str, Path] = {}
    errs: list[str] = []
    for s in skills:
        errs += check(s)
        try:
            n = parse_frontmatter(s.read_text(encoding="utf-8")).get("name")
            if n in names: errs.append(f"{s}: duplicate name '{n}' (also {names[n]})")
            elif n: names[n] = s
        except Exception:  # noqa: BLE001
            pass
    if errs:
        print("SKILL VALIDATION FAILED:\n" + "\n".join(f"  - {x}" for x in errs)); return 1
    print(f"OK: {len(skills)} skills valid, names unique."); return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 7.2 `.github/workflows/validate-skills.yml`

```yaml
name: validate-skills
on:
  pull_request:
    paths:
      - ".agents/skills/**"
      - ".agents/agents/**"
      - "templates/**"
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install pyyaml
      - name: Validate skill format + name uniqueness
        run: python tests/test_skill_format.py
      # Optional: official reference validator for spec-canonical checks
      # - run: skills-ref validate .agents/skills/**/
```

---

## 9. Consumption by reference (three mechanisms)

No copies are pushed anywhere. Consumers point back at the central repo. Pick per use case:

**A. Personal install (per developer) — `gh skill`**
```bash
# one-time: install the DIP skills into your personal scope (~/.copilot/skills)
gh skill install dip-org/dip-agentic-tools --path .agents/skills --pin v1.0.0
# later: pull a newer release
gh skill update
```
Skills then work in **every** repo you open. `gh skill` writes provenance (source repo, ref, SHA)
into each `SKILL.md` so updates are traceable, and `--pin` locks a version.

**B. Agent location (per developer/workspace) — VS Code setting**
```jsonc
// settings.json — point at a local clone of dip-agentic-tools
"chat.agentFilesLocations": [
  "/abs/path/to/dip-agentic-tools/.agents/agents"
]
```
The engineer/orchestrator personas load from the central clone; `git pull` updates them.

**C. Plugin install (team-wide) — Copilot CLI**
```bash
# installs agents + skills together from plugin.json
copilot plugin install dip-org/dip-agentic-tools
```

> **Recommendation:** standardize on **A + C pinned to a release tag** for reproducibility, and
> use **B** for engineers actively iterating on the agents themselves.

---

## 10. Versioning & release policy

Reference-consumption means everyone can pull from one place — so a bad merge can hit everyone at
once. Control it with releases.

- **Semantic tags**: `v1.0.0`, `v1.1.0`, `v2.0.0`. Bump **minor** for new skills/agents,
  **patch** for fixes to existing ones, **major** for renames or breaking routing changes.
- **`CHANGELOG.md` is mandatory** and consumer-facing: every entry says what changed and whether
  a consumer needs to re-pin.
- **Consumers pin** (`--pin v1.0.0`) and upgrade deliberately after reading the changelog.
- **`main` is the bleeding edge**; only tagged releases are "blessed." CI (`validate-skills.yml`)
  gates `main`; releases are cut from green `main`.
- **Deprecation**: when renaming a skill, keep the old name as a thin alias for one minor version
  with a deprecation note in its description, then remove it in the next major.

---

## 11. Step-by-step SDLC walkthrough (with expected inputs & outputs)

A concrete run of DIP-1234, every stage annotated with what goes in and what comes out.

### Step 0 — Setup (one-time, per developer)
- **Input:** access to `dip-agentic-tools`.
- **Action:** `gh skill install dip-org/dip-agentic-tools --path .agents/skills --pin v1.0.0`;
  set `chat.agentFilesLocations` to the agents folder.
- **Output:** skills available in every repo; agents appear in the VS Code picker.

### Step 1 — Start from the story
- **Input (developer prompt):** *"Start work on DIP-1234."* with `dip-ings-orchestrator` selected.
- **Action:** orchestrator activates `jira-story-breakdown`; the skill calls
  `jira-ops/get_issue("DIP-1234")`.
- **Output:** the full story text in context (title, description, acceptance criteria).

### Step 2 — Assess & decompose
- **Input:** the fetched story + `references/sizing-rubric.md`.
- **Action:** skill scores size (large — spans app-config + dag-config) and splits into 3 subtasks.
- **Output:** `/tmp/DIP-1234-plan.json` (the §6.1 plan).

### Step 3 — Validate the plan
- **Input:** the plan JSON.
- **Action:** `python scripts/validate_plan.py /tmp/DIP-1234-plan.json`.
- **Output:** `OK: plan is valid and acyclic.` (If invalid, the skill reads the errors, fixes the
  plan, and re-runs — a validation loop.)

### Step 4 — Human approval gate 🧑
- **Input:** the presented plan.
- **Action:** developer reviews the breakdown and dependency order; edits or approves.
- **Output:** approval signal. **No code has been written yet.**

### Step 5 — Dispatch subtask 1 (no dependencies, repo: progectai-ingestion)
- **Input:** subtask `DIP-1234-1` (add jobs for customers + orders).
- **Action:** orchestrator hands off to `dip-ings-app-config-engineer` (runs as a **subagent**,
  own context) in the **`progectai-ingestion`** working tree. The agent activates `add-job`, runs
  plan→validate→execute twice, then `validate-app-config`, and opens a PR.
- **Output:** `configs/jobs/crm/customers.yaml` + `configs/jobs/crm/orders.yaml`, validator-passed;
  **PR `progectai-ingestion#101`** opened. Orchestrator writes `{status: in_review, pr_url}` onto
  subtask 1 in the Jira story. Example of one file:
  ```yaml
  source: CRM
  job_name: crm_customers
  target_bq_table: ${GCP_PROJECT}.crm.customers
  load_mode: incremental
  watermark_col: updated_at
  partition_col: ingested_date
  ```

### Step 6 — Dispatch subtask 2 (depends on 1, SAME repo)
- **Gate:** subtask 2 is in the **same repo** as subtask 1 (`depends_on_merge: false`), so it does
  **not** require a merge — it only needs 1's work present locally. It may even ride in the same PR.
- **Input:** subtask `DIP-1234-2` (orders enrichment SQL).
- **Action:** same `dip-ings-app-config-engineer` activates `add-sql`.
- **Output:** `configs/sql/orders_enrich.sql`, validator-passed; added to PR `#101` (or a sibling
  PR `#102`). Status written back to the story.

  ⏳ **HUMAN reviews & MERGES the progectai-ingestion PR(s).** CODEOWNERS + CI for that repo.
  Orchestrator updates subtasks 1 & 2 to `status: merged`. **The live session may end here.**

### Step 7 — Dispatch subtask 3 (depends on 1 & 2, DIFFERENT repo → MERGE GATE)
- **Gate:** subtask 3 is in **`progectai-dag`**, a different repo from its dependencies
  (`depends_on_merge: true`). The orchestrator checks PR status via `github/get_pull_request` for
  subtasks 1 & 2. It dispatches **only when both are `merged`**. If they aren't yet, it records
  state and stops — the developer resumes later.
- **Resume:** developer says *"continue DIP-1234"*. The orchestrator re-reads the Jira story
  (**not** the dead plan in `/tmp`), sees 1 & 2 are merged, and proceeds. No re-planning, no rework.
- **Input:** subtask `DIP-1234-3` (daily DAG).
- **Action:** hands off to `dip-ings-dag-config-engineer` in the **`progectai-dag`** working tree;
  it activates `add-dag` + `add-task`, referencing the now-**merged** job names, then
  `validate-dag-config`, and opens a PR.
- **Output:** `dags/daily_crm_dag.json` referencing `crm_customers` + `crm_orders`, scheduled
  daily, validator-passed; **PR `progectai-dag#201`** opened. Status written to the story.

### Step 8 — Review & ticket update
- **Input:** all produced files across both repos; `pull_request_template.md`.
- **Action:** `review-pr` drafts each PR body; `jira-ticket-writer` keeps DIP-1234 subtask status
  current.
- **Output:** ready PR descriptions and an up-to-date Jira story.

### Step 9 — PR & CI (per repo) 🧑
- **Input:** the open PRs (`progectai-ingestion#101/#102`, then `progectai-dag#201`).
- **Action:** each repo's own CI runs unit tests + re-runs domain validators; that repo's
  CODEOWNERS review.
- **Output:** green checks + approvals → **merge**. When the last subtask merges, the orchestrator
  marks the Jira story Done.

> At no point did a skill write code. `jira-story-breakdown` produced a plan; the engineer agents,
> using their domain skills, produced the code. That separation is what makes the system testable,
> auditable, and safe.

---

## 12. Build & migration sequence (priority order)

1. **Fix `templates/skill-template.md`** to the §5.6 gold standard. Everything inherits it.
2. **Stand up the CI gate**: `tests/test_skill_format.py` + `validate-skills.yml`. Run once over
   all existing skills to get a defect + naming-collision list.
3. **Apply the v2 renames** (five buckets, collision-safe names). Add deprecation aliases for any
   skill names already referenced elsewhere.
4. **Fix `pipeline-builder`** (the 4 known fixes); re-validate.
5. **Add eval cases for `jira-ticket-writer`**: run against 5–10 real tickets, grade vs. actual,
   fold the delta into a Gotchas section.
6. **Build the agent layer** (`.agents/agents/`): the 4 engineer agents + the orchestrator +
   `agent-template.agent.md`.
7. **Build `jira-story-breakdown`** + `validate_plan.py` + `sizing-rubric.md`. Decide and encode
   the concrete "huge work" thresholds.
8. **Wire MCP**: `jira-ops` and `github` (Cloud Run/Rovo HTTP) into the orchestrator so it can
   read story state and PR merge status; `pyspark-ops` into the app engineer and `debug-pipeline`.
   Make the orchestrator resumable (Jira story as state store) and enforce cross-repo merge gates.
9. **Migrate instructions** into `instructions/<domain>/` (pyspark, progectai-dag, composer; author
   the new app-config one from scratch).
10. **Build the 5 new `dag/` skills** using the real-execution-first method (write a real
    operator/sensor/service/generator with an agent, capture corrections, extract the pattern).
11. **Switch consumers to reference mode** (§8), pin to a tagged release, retire any old per-repo
    skill copies.
12. **Package & tag `v1.0.0`**, publish `plugin.json`, write the first `CHANGELOG.md` entry.

---

## 13. Maturity checklist

| # | Standard | Target |
|---|----------|--------|
| 1 | Four layers cleanly separated (instructions / principles / skills / agents) | ✅ designed |
| 2 | All `SKILL.md` pass spec validation (name=dir, ≤64, desc≤1024, ≤500 lines) | CI gate |
| 3 | Skill names globally unique (flat-install safe) | CI gate |
| 4 | Gold-standard template enforced for new skills | fix template first |
| 5 | Every skill has a Gotchas section grown from real corrections | per skill |
| 6 | Agent layer exists; personas route to skills + scope tools | build `.agents/agents/` |
| 7 | Orchestrator + jira-story-breakdown implement plan→approve→route | build |
| 8 | Cross-repo subtasks gated on MERGE; orchestrator resumable via Jira state | build orchestrator + github MCP |
| 9 | Live ops via MCP (static tool surface documented), not faked in skills | wire jira/github/pyspark-ops |
| 10 | Single CI quality gate on every PR | validate-skills.yml |
| 11 | Consumption by reference; no per-repo copies | switch consumers |
| 12 | Semantic versioning + consumer-facing CHANGELOG; consumers pin | release policy |
| 13 | Least-privilege: agents scope `tools`; secrets via GSM/Actions secrets | per agent |
| 14 | Evals for non-deterministic skills (jira-ticket-writer, genai-app) | add eval cases |
| 15 | Installable plugin + `llms.txt` + CONTRIBUTING + CHANGELOG | package & publish |

---

*Conforms to the open Agent Skills standard (agentskills.io) and the GitHub Copilot custom agents
format. Portable across Copilot (VS Code / CLI / cloud), Claude Code, Cursor, and other
skills-compatible clients. The Jira skill plans; the agents build.*
