#!/usr/bin/env python3
"""Validate an ingestion job YAML against DIP app-config rules (stdlib only).

Usage: validate_job.py <job.yaml> <ingestion-repo-root>

Rules enforced (mirrors .principles/app-config/anti-patterns.md):
- required keys: source, job_name, target_bq_table, load_mode
- target_bq_table: three-part, starts with ${GCP_PROJECT}., NOT quoted
- load_mode in {full, incremental, cdc}
- incremental/cdc require watermark_col; cdc must OMIT partition_col
- source must exist (case-sensitive) in references/source-registry.md
"""
import re
import sys
from pathlib import Path

REQUIRED = ["source", "job_name", "target_bq_table", "load_mode"]
LOAD_MODES = {"full", "incremental", "cdc"}


def parse_simple_yaml(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].rstrip()
        if not line or ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def registry_sources(repo_root: Path) -> set:
    reg = repo_root / "references" / "source-registry.md"
    if not reg.exists():
        return set()
    srcs = set()
    for line in reg.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([A-Za-z0-9_-]+)\s*\|", line)
        if m and m.group(1).lower() not in ("source",):
            srcs.add(m.group(1))
    return srcs


def validate(job_file: Path, repo_root: Path) -> list[str]:
    errs = []
    cfg = parse_simple_yaml(job_file.read_text(encoding="utf-8"))

    for k in REQUIRED:
        if not cfg.get(k):
            errs.append(f"missing required key: {k}")
    if errs:
        return errs

    tbl = cfg["target_bq_table"]
    if tbl.startswith(('"', "'")):
        errs.append("target_bq_table must NOT be quoted - "
                    "${GCP_PROJECT} resolves only when unquoted")
    if not tbl.strip("'\"").startswith("${GCP_PROJECT}."):
        errs.append("target_bq_table must start with ${GCP_PROJECT}. (three-part)")
    elif tbl.strip("'\"").count(".") != 2:
        errs.append("target_bq_table must be three-part: ${GCP_PROJECT}.dataset.table")

    mode = cfg["load_mode"]
    if mode not in LOAD_MODES:
        errs.append(f"load_mode '{mode}' invalid (full|incremental|cdc)")
    if mode in ("incremental", "cdc") and not cfg.get("watermark_col"):
        errs.append(f"load_mode '{mode}' requires watermark_col")
    if mode == "cdc" and cfg.get("partition_col"):
        errs.append("cdc mode must OMIT partition_col (ignored + warns)")

    srcs = registry_sources(repo_root)
    if srcs and cfg["source"] not in srcs:
        errs.append(f"source '{cfg['source']}' not in source-registry.md "
                    f"(case-sensitive; known: {sorted(srcs)})")
    return errs


if __name__ == "__main__":
    f, root = Path(sys.argv[1]), Path(sys.argv[2])
    errors = validate(f, root)
    if errors:
        print(f"JOB INVALID ({f.name}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: {f.name} passes all app-config rules.")
