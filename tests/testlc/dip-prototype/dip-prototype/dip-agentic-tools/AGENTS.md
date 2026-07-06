# DIP Agentic Tools (Prototype)

Central source of truth for the DIP (Data Ingestion Platform) agentic AI-SDLC.
This is a small-scale prototype of the full platform.

## Stack (non-negotiable)
- PySpark on Dataproc, Cloud Composer (Airflow), BigQuery sink. Confirm exact
  versions at runtime - never assume (PySpark 3.5->4.x and Airflow 2.x->3.x
  migrations are in flight).
- Never propose pandas for large-data transforms - use PySpark.

## Organization
- `.principles/` - the "why": architecture, anti-patterns, security.
- `skills/` - task workflows, auto-activated by description match.
- `agents/` - personas; start with dip-ings-supervisor for any Jira story.

## Hard rules
- Never hardcode GCP project IDs - always ${GCP_PROJECT}.
- Every config change must pass its domain validator before being called done.
- The Jira skill PLANS; the agents BUILD; cross-repo deps wait for MERGE.

## Routing
| Domain     | Repo (this prototype)     | Agent                          |
|------------|---------------------------|--------------------------------|
| app        | pyspark-ingestion-app     | dip-ings-app-engineer          |
| app-config | progectai-ingestion (*)        | dip-ings-app-config-engineer   |
| dag        | composer                  | dip-ings-dag-engineer          |
| dag-config | progectai-dag (*)              | dip-ings-dag-config-engineer   |

(*) app-config and dag-config repos are PROJECT-SPECIFIC - names vary per
project (e.g. progectai-ingestion / progectai-dag at work). app and dag repos
are FIXED and shared by all projects.

NOTE: `barricade-migrate` and `tsql-to-bq` are SERVICES of the ingestion app
(see pyspark-ingestion-app/etl/services/), NOT skills.
