---
name: validate-app-config
description: >
  Repo-wide validation of the ingestion config repo: every job YAML passes the
  job validator, job names are globally unique, and SQL references only
  three-part tables. Use after any config change and before every PR.
metadata:
  domain: app-config
  owner: dip-platform
  version: "0.1"
---

# Validate App Config (repo-wide)

Run the add-job validator across all configs/jobs/**/*.yaml and check
cross-file collisions (duplicate job_name).
