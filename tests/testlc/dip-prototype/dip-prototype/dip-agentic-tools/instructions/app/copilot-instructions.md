# PySpark Ingestion App - Copilot Instructions

You are in the SHARED PySpark ingestion application repo (all projects use it).
- Confirm the PySpark version before version-sensitive code (3.5 -> 4.x in flight).
- Never SparkSession.builder / print() / logging.getLogger() directly - use the
  app singletons and EdhPySparkLogger equivalents.
- barricade_migrate_service and tsql_to_bq_service are SERVICES here, not skills.
- Every change: unit test + validate before PR; two-layer review (AI then human).
