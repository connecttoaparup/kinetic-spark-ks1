# Ingestion Config Repo - Copilot Instructions

You are in a PROJECT-SPECIFIC ingestion **config** repo. Assets are YAML/SQL
(jobs, pipelines, transforms). You are NOT editing PySpark app code here.
1. Match the request to a skill (add-job / add-sql / validate-app-config).
2. Before declaring done, run validate-app-config.
3. Conventions: one job per file configs/jobs/<source>/<job_name>.yaml;
   three-part ${GCP_PROJECT}.dataset.table, unquoted; incremental/cdc need
   watermark_col; cdc omits partition_col; source must exist in
   references/source-registry.md (case-sensitive).
