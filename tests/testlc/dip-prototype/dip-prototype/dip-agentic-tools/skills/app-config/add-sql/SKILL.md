---
name: add-sql
description: >
  Add a SQL transform file to the project's ingestion config repo under
  configs/sql/. Use when asked to "add a SQL", create an enrichment or
  transform query for an ingestion job.
metadata:
  domain: app-config
  owner: dip-platform
  version: "0.1"
---

# Add SQL Transform

1. Write the SQL to configs/sql/<name>.sql with a header comment
   (ticket, purpose, source job).
2. Only reference tables via ${GCP_PROJECT}. three-part names.
3. Confirm with validate-app-config.

## Gotchas
- No SELECT * in committed transforms - list columns.
