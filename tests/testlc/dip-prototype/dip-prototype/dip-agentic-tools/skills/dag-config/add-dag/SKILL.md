---
name: add-dag
description: >
  Add a new DAG JSON config to the project's dag-config repo, scheduling
  ingestion jobs via the shared plugin framework. Use when asked to "add a
  dag", "schedule jobs", or create a pipeline schedule.
metadata:
  domain: dag-config
  owner: dip-platform
  version: "0.1"
---

# Add DAG Config

## Workflow (plan -> validate -> execute)
1. Gather: dag_id, schedule, list of job_names to schedule.
2. Plan: write JSON to a temp path.
3. Validate: `python scripts/validate_dag_config.py <file> <ingestion-repo-root>`
   - every referenced job_name MUST exist as a merged job YAML.
4. Execute: move to dags/<dag_id>.json. Confirm with validate-dag-config.

## Gotchas
- NEVER reference a job that is not merged in the ingestion-config repo -
  this is exactly why the cross-repo merge gate exists.
