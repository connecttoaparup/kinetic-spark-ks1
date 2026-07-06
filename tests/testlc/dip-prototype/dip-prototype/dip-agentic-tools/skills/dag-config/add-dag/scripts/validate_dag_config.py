#!/usr/bin/env python3
"""Validate a DAG JSON config against DIP dag-config rules (stdlib only).

Usage: validate_dag_config.py <dag.json> <ingestion-repo-root>

Rules:
- JSON well-formed; dag_id and schedule_interval present
- at least one task; every task has task_id + job_name
- EVERY referenced job_name must exist as a job YAML in the ingestion repo
  (this is the cross-repo merge gate made concrete: a DAG may only reference
  jobs that are actually merged).
"""
import json
import sys
from pathlib import Path


def merged_job_names(ingestion_root: Path) -> set:
    names = set()
    for y in (ingestion_root / "configs" / "jobs").rglob("*.yaml"):
        for line in y.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("job_name:"):
                names.add(line.split(":", 1)[1].strip())
    return names


def validate(dag_file: Path, ingestion_root: Path) -> list[str]:
    errs = []
    try:
        dag = json.loads(dag_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        return [f"invalid JSON: {ex}"]

    if not dag.get("dag_id"):
        errs.append("missing dag_id")
    if not dag.get("schedule_interval"):
        errs.append("missing schedule_interval")
    tasks = dag.get("tasks", [])
    if not tasks:
        errs.append("DAG has no tasks")

    known = merged_job_names(ingestion_root)
    for t in tasks:
        tid, job = t.get("task_id"), t.get("job_name")
        if not tid or not job:
            errs.append(f"task entry missing task_id/job_name: {t}")
            continue
        if job not in known:
            errs.append(f"task '{tid}' references job '{job}' which does NOT "
                        f"exist in the ingestion repo - cross-repo merge gate "
                        f"violation (known: {sorted(known)})")
    return errs


if __name__ == "__main__":
    f, root = Path(sys.argv[1]), Path(sys.argv[2])
    errors = validate(f, root)
    if errors:
        print(f"DAG INVALID ({f.name}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: {f.name} passes all dag-config rules (all job refs exist).")
