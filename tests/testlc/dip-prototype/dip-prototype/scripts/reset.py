#!/usr/bin/env python3
"""Reset the demo: story state, PR db, generated files, and git branches."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "mcp-servers" / "data"
GIT_ID = ["-c", "user.name=dip-reset", "-c", "user.email=dip@local"]

# story
story = json.loads((DATA / "DIP-1234.json").read_text())
story["state"] = {"plan_approved": False, "subtasks": []}
(DATA / "DIP-1234.json").write_text(json.dumps(story, indent=2) + "\n")

# prs
(DATA / "prs.json").write_text(json.dumps({
    "progectai-ingestion": {"next": 101, "prs": {}},
    "progectai-dag": {"next": 201, "prs": {}},
    "pyspark-ingestion-app": {"next": 1, "prs": {}},
    "composer": {"next": 1, "prs": {}},
}, indent=2) + "\n")

# git: hard-reset main to the initial commit, delete feature branches
for repo in ["progectai-ingestion", "progectai-dag",
             "pyspark-ingestion-app", "composer"]:
    cwd = ROOT / "repos" / repo
    def g(*a, ok=True):
        p = subprocess.run(["git", *GIT_ID, *a], cwd=cwd,
                           capture_output=True, text=True)
        if ok and p.returncode != 0:
            print(f"[{repo}] git {' '.join(a)}: {p.stderr.strip()}")
        return p.stdout.strip()
    g("checkout", "main")
    first = g("rev-list", "--max-parents=0", "HEAD").splitlines()[0]
    g("reset", "--hard", first)
    for br in g("branch", "--format=%(refname:short)").splitlines():
        if br and br != "main":
            g("branch", "-D", br)
print("Reset complete: story, PRs, repos back to initial state.")
