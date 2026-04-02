"""
_AIRFLOW_agent/tools.py

Tools the _AIRFLOW Platform Engineering Agent can call.

In Google ADK, tools are plain Python functions decorated with @tool.
ADK automatically:
- Shows these tools to Gemini as callable functions
- Calls them when Gemini decides to use a tool
- Returns the result back to Gemini to continue reasoning

Each function docstring is what Gemini reads to decide
WHEN and HOW to use the tool — write them clearly.
"""

from __future__ import annotations

import base64
import os
import re
import subprocess
from pathlib import Path

import requests

# ── Config from environment ───────────────────────────────────────────────────
GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
DAG_REPO_OWNER  = os.environ.get("DAG_REPO_OWNER", "")
DAG_REPO_NAME   = os.environ.get("DAG_REPO_NAME", "")
PLUGIN_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "")
PLUGIN_REPO_NAME  = os.environ.get("GITHUB_REPO_NAME", "")

GITHUB_HEADERS = {
    "Authorization":        f"Bearer {GITHUB_TOKEN}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ── Path helpers ──────────────────────────────────────────────────────────────
def _repo_root() -> Path:
    """Find the repo root — 2 levels up from this file."""
    return Path(__file__).parent.parent.resolve()

def _instructions_dir() -> Path:
    return _repo_root() / ".github" / "instructions"


# =============================================================================
# SKILL TOOLS — reads your .github/instructions/*.md files
# =============================================================================

def load_instruction_skill(layer: str) -> str:
    """
    Load the instruction rules for a specific code layer.

    Use this when reviewing code or answering questions about a specific layer.
    The layer name maps to a .github/instructions/{layer}.instructions.md file.

    Args:
        layer: One of: operators, sensors, service, utility, generator,
               python, pr-review, copilot (for repo-wide rules)

    Returns:
        The full instruction rules for that layer as text.
    """
    # Map friendly names to file names
    file_map = {
        "operators":   "operators.instructions.md",
        "sensors":     "sensors.instructions.md",
        "service":     "service.instructions.md",
        "utility":     "utility.instructions.md",
        "generator":   "generator.instructions.md",
        "python":      "python.instructions.md",
        "pr-review":   "pr-review.instructions.md",
        "copilot":     "copilot-instructions.md",
    }

    # Normalise layer name
    layer = layer.lower().strip()
    filename = file_map.get(layer)

    if not filename:
        return (
            f"Unknown layer '{layer}'. "
            f"Valid options: {', '.join(file_map.keys())}"
        )

    # Try instructions dir first, then repo root for copilot-instructions
    instructions_dir = _instructions_dir()
    file_path = instructions_dir / filename
    if not file_path.exists():
        file_path = _repo_root() / ".github" / filename

    if not file_path.exists():
        return f"Instruction file not found: {file_path}"

    content = file_path.read_text(encoding="utf-8")
    return f"## Skill: {layer}\n\n{content}"


def list_available_skills() -> str:
    """
    List all available instruction skills loaded from .github/instructions/.

    Use this when the user asks what rules or skills the agent knows about,
    or at the start of a review to understand what's available.

    Returns:
        List of skill names and their file sizes.
    """
    instructions_dir = _instructions_dir()
    if not instructions_dir.exists():
        return "Instructions directory not found: .github/instructions/"

    skills = []
    for f in sorted(instructions_dir.glob("*.instructions.md")):
        size = f.stat().st_size
        skills.append(f"- **{f.stem}** ({size:,} chars) — `{f.name}`")

    # Also check copilot-instructions.md in parent
    main_instructions = _repo_root() / ".github" / "copilot-instructions.md"
    if main_instructions.exists():
        size = main_instructions.stat().st_size
        skills.append(f"- **copilot** ({size:,} chars) — `copilot-instructions.md`")

    return "## Available Skills\n\n" + "\n".join(skills)


# =============================================================================
# CODE REVIEW TOOLS
# =============================================================================

def read_local_file(file_path: str) -> str:
    """
    Read the content of a local Python file from the repository.

    Use this when the user asks to review a specific file, or when
    you need to see the actual code before reviewing it.

    Args:
        file_path: Relative path from repo root, e.g. "_AIRFLOW_plugins/operators/dataproc.py"

    Returns:
        File content as text, or an error message if not found.
    """
    full_path = _repo_root() / file_path
    if not full_path.exists():
        return f"File not found: {file_path}"
    if not full_path.suffix == ".py":
        return f"Only .py files are supported for review. Got: {file_path}"

    content = full_path.read_text(encoding="utf-8")
    return f"## File: {file_path}\n\n```python\n{content}\n```"


def get_git_diff(base_branch: str = "main") -> str:
    """
    Get the git diff between the current branch and a base branch.

    Use this when the user asks to review their current changes,
    check what they've modified, or simulate a PR review locally.

    Args:
        base_branch: Branch to compare against. Default is "main".

    Returns:
        Git diff of all changed Python files.
    """
    try:
        # Get current branch name
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(_repo_root())
        )
        current_branch = branch_result.stdout.strip()

        # Get diff
        diff_result = subprocess.run(
            ["git", "diff", f"origin/{base_branch}...{current_branch}", "--", "*.py"],
            capture_output=True, text=True, cwd=str(_repo_root())
        )

        diff = diff_result.stdout
        if not diff.strip():
            return f"No Python file changes detected between '{current_branch}' and '{base_branch}'."

        return (
            f"## Git Diff: {current_branch} → {base_branch}\n\n"
            f"```diff\n{diff[:6000]}\n```"
            + ("\n*(truncated — showing first 6000 chars)*" if len(diff) > 6000 else "")
        )
    except Exception as e:
        return f"Error reading git diff: {e}"


# =============================================================================
# GITHUB DAG REPO TOOLS
# =============================================================================

def scan_dag_repo_for_operator(operator_name: str) -> str:
    """
    Search the DAG repository for all pipelines that use a specific operator.

    Use this when:
    - A developer asks "which DAGs use DataprocOperator?"
    - Checking if a change to an operator will break any DAGs
    - Understanding the impact of removing or modifying an operator parameter

    Args:
        operator_name: The operator class name to search for,
                       e.g. "DataprocOperator", "GCSFileSensor"

    Returns:
        List of pipeline names and files that reference this operator.
    """
    if not all([GITHUB_TOKEN, DAG_REPO_OWNER, DAG_REPO_NAME]):
        return (
            "GitHub credentials not configured. "
            "Set GITHUB_TOKEN, DAG_REPO_OWNER, DAG_REPO_NAME in .env"
        )

    try:
        # Get all pipeline subfolders in dags/
        response = requests.get(
            f"https://api.github.com/repos/{DAG_REPO_OWNER}/{DAG_REPO_NAME}/contents/dags",
            headers=GITHUB_HEADERS, timeout=30
        )
        response.raise_for_status()
        pipelines = [p for p in response.json() if p["type"] == "dir"]

        findings = []
        for pipeline in pipelines:
            # Read platform_dag.py
            dag_resp = requests.get(
                f"https://api.github.com/repos/{DAG_REPO_OWNER}/{DAG_REPO_NAME}"
                f"/contents/{pipeline['path']}/platform_dag.py",
                headers=GITHUB_HEADERS, timeout=30
            )
            if dag_resp.status_code != 200:
                continue

            content = base64.b64decode(
                dag_resp.json().get("content", "")
            ).decode("utf-8", errors="replace")

            if operator_name in content:
                # Find matching lines
                lines = [
                    f"  line {i+1}: `{line.strip()}`"
                    for i, line in enumerate(content.splitlines())
                    if operator_name in line
                ]
                findings.append(
                    f"**{pipeline['name']}**\n" + "\n".join(lines[:3])
                )

        if not findings:
            return f"No DAG pipelines found using `{operator_name}`."

        return (
            f"## DAGs using `{operator_name}`\n\n"
            f"Found in **{len(findings)}** pipeline(s):\n\n"
            + "\n\n".join(findings)
        )

    except requests.HTTPError as e:
        return f"GitHub API error: {e}"


def get_dag_plugin_versions() -> str:
    """
    Get the current plugin_version used by each DAG pipeline.

    Use this when:
    - A developer asks "which version are DAGs currently on?"
    - Checking if DAGs need to be updated after a new wheel version
    - Understanding the version distribution across teams

    Returns:
        Table showing each pipeline and its current plugin_version.
    """
    if not all([GITHUB_TOKEN, DAG_REPO_OWNER, DAG_REPO_NAME]):
        return "GitHub credentials not configured."

    try:
        response = requests.get(
            f"https://api.github.com/repos/{DAG_REPO_OWNER}/{DAG_REPO_NAME}/contents/dags",
            headers=GITHUB_HEADERS, timeout=30
        )
        response.raise_for_status()
        pipelines = [p for p in response.json() if p["type"] == "dir"]

        rows = []
        for pipeline in pipelines:
            conf_resp = requests.get(
                f"https://api.github.com/repos/{DAG_REPO_OWNER}/{DAG_REPO_NAME}"
                f"/contents/{pipeline['path']}/platform_conf.json",
                headers=GITHUB_HEADERS, timeout=30
            )
            if conf_resp.status_code != 200:
                rows.append(f"| `{pipeline['name']}` | ❓ not found |")
                continue

            import json
            conf = json.loads(
                base64.b64decode(conf_resp.json().get("content", "")).decode("utf-8")
            )
            version = conf.get("props", {}).get("plugin_version", "not set")
            rows.append(f"| `{pipeline['name']}` | `{version}` |")

        return (
            "## Plugin Version Distribution\n\n"
            "| Pipeline | plugin_version |\n"
            "|---|---|\n"
            + "\n".join(rows)
        )

    except Exception as e:
        return f"Error fetching plugin versions: {e}"


def get_changelog() -> str:
    """
    Read the CHANGELOG.md from the airflow_plugins repo.

    Use this when a developer asks:
    - "What changed in the latest version?"
    - "What was added in v1.2.0?"
    - "What are the breaking changes?"

    Returns:
        The content of CHANGELOG.md, truncated to recent versions.
    """
    changelog_path = _repo_root() / "CHANGELOG.md"
    if not changelog_path.exists():
        return "CHANGELOG.md not found in repo root."

    content = changelog_path.read_text(encoding="utf-8")
    # Return first 3000 chars — covers recent versions
    return content[:3000] + ("\n*(truncated)*" if len(content) > 3000 else "")
