---
name: add-job
description: >
  Add a new ingestion job to the project's ingestion YAML config repo. Use when
  onboarding a table/source, creating a job definition, or configuring
  full/incremental/cdc loading. Produces a validated job YAML.
metadata:
  domain: app-config
  owner: dip-platform
  version: "0.1"
---

# Add an Ingestion Job

## Workflow (plan -> validate -> execute)
1. Gather: source, job_name, target_bq_table, load_mode, watermark_col.
2. Plan: write YAML to a temp path.
3. Validate: `python scripts/validate_job.py <file> <repo-root>`; loop to pass.
4. Execute: move to configs/jobs/<source>/<job_name>.yaml.
5. Confirm with validate-app-config.

## Gotchas
- target_bq_table must be three-part `${GCP_PROJECT}.dataset.table`, unquoted.
- incremental/cdc REQUIRE watermark_col. cdc must OMIT partition_col.
- source is case-sensitive and must exist in references/source-registry.md.
