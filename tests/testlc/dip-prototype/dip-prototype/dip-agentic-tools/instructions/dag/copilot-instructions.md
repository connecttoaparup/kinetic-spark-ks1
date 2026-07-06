# Airflow Plugin Framework - Copilot Instructions

You are in the SHARED composer plugin repo (all projects consume it).
- Confirm the Airflow version (2.x vs 3.x) before operators/provider imports.
- Backward compatibility is a hard requirement - breaking changes need a
  MAJOR bump with migration notes for every DAG team.
