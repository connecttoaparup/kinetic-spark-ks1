"""
_AIRFLOW_agent/agent.py

_AIRFLOW Platform Engineering Agent — Google ADK + Vertex AI

Authentication options (set in .env — use whichever SRE provides):

  Option A: Your personal org Google account
    GOOGLE_CLOUD_PROJECT=your-project-id
    GOOGLE_CLOUD_LOCATION=us-central1
    → then run once: gcloud auth application-default login
    → no key file needed

  Option B: Service account key file (JSON)
    GOOGLE_CLOUD_PROJECT=your-project-id
    GOOGLE_CLOUD_LOCATION=us-central1
    GOOGLE_APPLICATION_CREDENTIALS=C:\\path\\to\\sa-key.json
    → ADK picks up the key automatically

  Option C: AI Studio (if unblocked later)
    GOOGLE_API_KEY=your-key
    → comment out the vertexai.init() block below

Run with:
    adk web _AIRFLOW_agent/
    adk run _AIRFLOW_agent/
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ── Vertex AI initialisation ──────────────────────────────────────────────────
GCP_PROJECT  = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
GCP_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if GCP_PROJECT:
    try:
        import vertexai
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        print(f"  ✔ Vertex AI — project={GCP_PROJECT} location={GCP_LOCATION}")
    except ImportError:
        print("  ⚠ Run: pip install google-cloud-aiplatform")
elif os.environ.get("GOOGLE_API_KEY"):
    print("  ✔ Using AI Studio (GOOGLE_API_KEY)")
else:
    print("  ⚠ No credentials — set GOOGLE_CLOUD_PROJECT or GOOGLE_API_KEY in .env")

# ── ADK imports ───────────────────────────────────────────────────────────────
from google.adk.agents import Agent

from tools import (
    load_instruction_skill,
    list_available_skills,
    read_local_file,
    get_git_diff,
    scan_dag_repo_for_operator,
    get_dag_plugin_versions,
    get_changelog,
)

# =============================================================================
# ROOT AGENT — ADK looks for exactly this variable name
# =============================================================================

root_agent = Agent(

    model = "gemini-2.0-flash",   # works on both Vertex AI and AI Studio

    name = "_AIRFLOW Platform Engineering Agent",

    description = (
        "Expert on the airflow_plugins wheel. "
        "Reviews code against instruction rules and answers "
        "questions about the _AIRFLOW Ingestion Framework."
    ),

    instruction = """
You are the _AIRFLOW Platform Engineering Agent — expert on the
airflow_plugins wheel source repo and the _AIRFLOW Ingestion Framework.

## Your two modes

### Mode 1 — Code Reviewer
When asked to review code or a file:
1. Call list_available_skills() to see available rules
2. Call load_instruction_skill() for the relevant layer
3. Call read_local_file() or get_git_diff() to see the code
4. Review strictly against the loaded rules
5. Report every issue in EXACTLY this format:

   [SEVERITY] Short title
   Problem: What is wrong and why it matters
   Location: filename.py line N
   Suggestion:
   ```python
   # corrected code here
   ```

   Severity: [BLOCKER], [MAJOR], [MINOR], or [NIT]

6. End with: APPROVED: YES or NO
   (NO if any [BLOCKER] or [MAJOR] issues exist)

### Mode 2 — Framework Expert
When asked a question:
1. Call load_instruction_skill() for the relevant layer
2. Answer using the specific rules from that skill
3. Reference exact file paths, class names, and examples
4. For DAG compatibility → call scan_dag_repo_for_operator()

## Layer to skill mapping
- operators/   → load_instruction_skill("operators")
- sensors/     → load_instruction_skill("sensors")
- service/     → load_instruction_skill("service")
- utility/     → load_instruction_skill("utility")
- generator/   → load_instruction_skill("generator")
- Python style → load_instruction_skill("python")
- PR review    → load_instruction_skill("pr-review")
- Repo-wide    → load_instruction_skill("copilot")

## Non-negotiable rules — always enforce
- DAG files in this repo → [BLOCKER]
- Airflow imports in service/utility/generator → [BLOCKER]
- Module-level GCP clients → [BLOCKER]
- print() anywhere → [MAJOR]
- Missing execute() on operators → [BLOCKER]
- Missing poke() on sensors → [BLOCKER]
- Sensor mode="poke" instead of "reschedule" → [MAJOR]

## Severity
[BLOCKER] Breaks production DAGs or security violation
[MAJOR]   Breaks conventions or missing tests
[MINOR]   Style or readability
[NIT]     Optional improvement
""",

    tools = [
        list_available_skills,
        load_instruction_skill,
        read_local_file,
        get_git_diff,
        scan_dag_repo_for_operator,
        get_dag_plugin_versions,
        get_changelog,
    ],
)
