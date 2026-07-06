#!/usr/bin/env python3
"""Validate a jira-story-breakdown execution plan before any handoff.
Checks: domains valid, owner_agent + repo match the routing table,
depends_on references exist, depends_on_merge set correctly for cross-repo
deps, and the dependency graph is acyclic (Kahn's algorithm)."""
import json
import sys

VALID_DOMAINS = {"common", "app", "app-config", "dag", "dag-config"}
DOMAIN_TO_AGENT = {
    "app": "dip-ings-app-engineer",
    "app-config": "dip-ings-app-config-engineer",
    "dag": "dip-ings-dag-engineer",
    "dag-config": "dip-ings-dag-config-engineer",
}
# Prototype repo map. app/dag are FIXED; app-config/dag-config are
# PROJECT-SPECIFIC (progectai-* here; name varies per project).
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
        dom, repo = s.get("domain"), s.get("repo")
        if dom not in VALID_DOMAINS:
            errs.append(f"{sid}: invalid domain '{dom}'")
        else:
            if dom in DOMAIN_TO_AGENT and s.get("owner_agent") != DOMAIN_TO_AGENT[dom]:
                errs.append(f"{sid}: owner_agent should be "
                            f"'{DOMAIN_TO_AGENT[dom]}' for '{dom}'")
            if dom in DOMAIN_TO_REPO and repo != DOMAIN_TO_REPO[dom]:
                errs.append(f"{sid}: repo should be "
                            f"'{DOMAIN_TO_REPO[dom]}' for domain '{dom}'")
        cross = False
        for dep in s.get("depends_on", []):
            if dep not in ids:
                errs.append(f"{sid}: depends_on unknown subtask '{dep}'")
                continue
            if by_id[dep].get("repo") != repo:
                cross = True
        if cross and not s.get("depends_on_merge"):
            errs.append(f"{sid}: cross-repo dependency -> depends_on_merge must be true")
        if not cross and s.get("depends_on_merge"):
            errs.append(f"{sid}: depends_on_merge true but no dep crosses a repo")

    # cycle detection (Kahn)
    indeg = {s["id"]: 0 for s in subtasks}
    adj = {s["id"]: [] for s in subtasks}
    for s in subtasks:
        for dep in s.get("depends_on", []):
            if dep in adj:
                adj[dep].append(s["id"])
                indeg[s["id"]] += 1
    q = [n for n, d in indeg.items() if d == 0]
    seen = 0
    while q:
        n = q.pop()
        seen += 1
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    if seen != len(subtasks):
        errs.append("dependency cycle detected - subtasks cannot be ordered")
    return errs


if __name__ == "__main__":
    errors = validate(sys.argv[1])
    if errors:
        print("PLAN INVALID:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("OK: plan is valid, acyclic, and cross-repo gates are correct.")
