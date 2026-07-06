# DAG Config Repo - Copilot Instructions

You are in a PROJECT-SPECIFIC dag-config repo. Assets are DAG JSON configs
consumed by the shared plugin.
1. Skills: add-dag / add-task / validate-dag-config.
2. A DAG may only reference job_names that exist MERGED in this project's
   ingestion-config repo - the validator enforces it (cross-repo merge gate).
