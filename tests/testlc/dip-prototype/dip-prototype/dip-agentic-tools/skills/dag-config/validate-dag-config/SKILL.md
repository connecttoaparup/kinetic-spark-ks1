---
name: validate-dag-config
description: >
  Repo-wide validation of the dag-config repo: JSON well-formed, dag_ids
  unique, and every task's job_name exists in the ingestion-config repo. Use
  after any DAG change and before every PR.
metadata:
  domain: dag-config
  owner: dip-platform
  version: "0.1"
---

# Validate DAG Config (repo-wide)

Run the add-dag validator across all dags/*.json.
