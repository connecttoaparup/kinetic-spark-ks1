# _AIRFLOW Agent — Google ADK Quick Start

## File structure (minimal — ADK only needs these 3)

```
_AIRFLOW_agent/
├── __init__.py   ← required by ADK
├── agent.py      ← ADK reads this — defines root_agent
└── tools.py      ← tool functions the agent calls
```

ADK looks for a variable named `root_agent` in `agent.py`.
That's the entire contract.

---

## Step 1 — Install

```bash
pip install google-adk
```

---

## Step 2 — Set up credentials

```
# Fill in _AIRFLOW_adk_agent/.env with your values:

GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GITHUB_TOKEN=ghp_your-token-here
DAG_REPO_OWNER=your-org
DAG_REPO_NAME=6953_us__AIRFLOW__AIRFLOWCS-_AIRFLOW-composer-airflow
GITHUB_REPO_OWNER=your-org
GITHUB_REPO_NAME=airflow-plugins-repo
```

> ⚠️ No API keys needed — uses Application Default Credentials (gcloud auth).
> Run once: `gcloud auth application-default login`

---

## Step 3 — Run with ADK web UI (easiest start)

```bash
# From your repo root
adk web _AIRFLOW_agent/
```

ADK starts a local server and opens a browser at `http://localhost:8000`

You'll see a chat UI — start talking to your agent immediately.

---

## What the ADK web UI looks like

```
┌─────────────────────────────────────────────────────┐
│  _AIRFLOW Platform Engineering Agent                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  Agent: Hello! I'm the _AIRFLOW Platform Engineering     │
│  Agent. I can review your code against the          │
│  instruction rules, or answer questions about       │
│  the airflow_plugins framework.                     │
│                                                     │
│  What would you like help with?                     │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  You: review operators/dataproc.py                  │
│                                                     │
│  Agent: [calls list_available_skills()]             │
│         [calls load_instruction_skill("operators")] │
│         [calls read_local_file("operators/...")]    │
│                                                     │
│  Found 2 issues:                                    │
│  [BLOCKER] Missing template_fields...               │
│  [MAJOR] print() found at line 45...               │
│                                                     │
│  APPROVED: NO                                       │
└─────────────────────────────────────────────────────┘
```

---

## Trigger options

### Option A — ADK web UI (browser, local) ← use this for testing
```powershell
adk web _AIRFLOW_adk_agent/
# → opens http://localhost:8000 in browser
# → full chat UI, see agent reasoning in real time
```

### Option B — ADK CLI (terminal, local)
```powershell
adk run _AIRFLOW_adk_agent/
# → interactive terminal chat, no browser needed
```

---

## Example conversations

### Review a file
```
You:   review _AIRFLOW_plugins/operators/dataproc.py

Agent: [calls load_instruction_skill("operators")]
       [calls read_local_file("_AIRFLOW_plugins/operators/dataproc.py")]

       Found 3 issues:

       [BLOCKER] Missing template_fields declaration
       Problem: gcp_project_id accepts Jinja templates but is not in template_fields
       Location: operators/dataproc.py line 28
       Suggestion:
         template_fields: Sequence[str] = ("gcp_project_id", "job_name")

       [MAJOR] print() found in operator
       Problem: print() output is not captured by Airflow task logs
       Location: line 45: print(f"Running job {self.job_name}")
       Suggestion: self.log.info("Running job %s", self.job_name)

       APPROVED: NO — fix blockers and major issues first
```

### Ask a framework question
```
You:   How do I write a new sensor for GCS?

Agent: [calls load_instruction_skill("sensors")]

       A GCS sensor must follow this pattern...
       [gives specific rules from sensors.instructions.md]
```

### Check DAG compatibility
```
You:   Which DAGs use DataprocOperator?

Agent: [calls scan_dag_repo_for_operator("DataprocOperator")]

       Found in 4 pipelines:
       - team_a/platform_dag.py line 45
       - team_b/platform_dag.py line 88
       ...
```

### Check what version DAGs are on
```
You:   What plugin versions are the DAGs currently using?

Agent: [calls get_dag_plugin_versions()]

       | Pipeline | plugin_version |
       |----------|----------------|
       | team_a   | 1.2.0          |
       | team_b   | 1.1.0          |  ← behind!
       | team_c   | 1.2.0          |
```

---

## How the tools map to your instruction files

| Tool | What it does | Maps to |
|---|---|---|
| `list_available_skills()` | Lists all .instructions.md files | All skills |
| `load_instruction_skill("operators")` | Reads operators.instructions.md | Operator rules |
| `load_instruction_skill("sensors")` | Reads sensors.instructions.md | Sensor rules |
| `load_instruction_skill("service")` | Reads service.instructions.md | Service rules |
| `load_instruction_skill("utility")` | Reads utility.instructions.md | Utility rules |
| `load_instruction_skill("python")` | Reads python.instructions.md | Python style |
| `load_instruction_skill("pr-review")` | Reads pr-review.instructions.md | PR checklist |
| `read_local_file(path)` | Reads actual source file | Code under review |
| `get_git_diff()` | Current branch diff | PR simulation |
| `scan_dag_repo_for_operator(name)` | GitHub API → DAG repo | Compatibility |
| `get_dag_plugin_versions()` | GitHub API → all platform_conf.json | Version distribution |
| `get_changelog()` | Reads CHANGELOG.md | Release history |
