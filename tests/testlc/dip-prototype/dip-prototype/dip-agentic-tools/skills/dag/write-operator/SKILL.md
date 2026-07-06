---
name: write-operator
description: >
  Generate a custom Airflow operator for the shared composer plugin framework.
  Use when asked to "write an operator" or add plugin capability. Confirm
  Airflow version (2.x vs 3.x) first - operator base APIs differ.
metadata:
  domain: dag
  owner: dip-platform
  version: "0.1"
---

# Write Operator (Prototype)

1. Confirm Airflow version with the user.
2. Scaffold operator under plugins/dip_ingestion_plugin/operators/.
3. Backward compatibility is a hard requirement - plugin is shared by all projects.
