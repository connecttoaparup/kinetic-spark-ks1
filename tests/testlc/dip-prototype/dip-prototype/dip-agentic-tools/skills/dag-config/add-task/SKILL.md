---
name: add-task
description: >
  Add task entries to an existing DAG JSON config in the dag-config repo. Use
  when asked to "add a task to the dag" or extend an existing schedule.
metadata:
  domain: dag-config
  owner: dip-platform
  version: "0.1"
---

# Add Task to DAG

1. Load the existing dags/<dag_id>.json.
2. Append the task entry {task_id, job_name}.
3. Re-run validate-dag-config.
