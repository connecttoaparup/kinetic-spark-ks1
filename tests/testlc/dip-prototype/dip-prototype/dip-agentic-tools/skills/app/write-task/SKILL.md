---
name: write-task
description: >
  Generate a PySpark Task class for the shared ingestion app (etl/pipeline/),
  registered in the TaskFactory. Use when asked to "write a task", "add a task
  type", or implement new pipeline logic. Confirm PySpark version first.
metadata:
  domain: app
  owner: dip-platform
  version: "0.1"
---

# Write Task (Prototype)

1. Confirm target PySpark version with the user (3.5 vs 4.x APIs differ).
2. Scaffold Task subclass; execute() returns Tuple[TaskStatus, Optional[Exception]].
3. Register the new TaskType in etl/pipeline/task_factory.py.
4. Generate a matching unit test.

## Gotchas
- Never SparkSession.builder directly - use the app singleton.
- barricade-migrate / tsql-to-bq are SERVICES (etl/services/), not tasks or skills.
