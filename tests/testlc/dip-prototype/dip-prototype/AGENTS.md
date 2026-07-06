# DIP AI-SDLC Workspace

This workspace contains the DIP platform central repo + the four domain repos
+ the local dev MCP servers. Start any Jira story with the
**dip-ings-supervisor** agent (select it from the Copilot Chat agent picker
dropdown - custom agents are NOT invoked with @ in VS Code).

## Routing (domain -> repo -> agent)
| Domain     | Repo                        | Agent                          |
|------------|-----------------------------|--------------------------------|
| app        | repos/pyspark-ingestion-app | dip-ings-app-engineer          |
| app-config | repos/progectai-ingestion   | dip-ings-app-config-engineer   |
| dag        | repos/composer              | dip-ings-dag-engineer          |
| dag-config | repos/progectai-dag         | dip-ings-dag-config-engineer   |

app/dag repos are FIXED (shared by all projects); app-config/dag-config repos
are PROJECT-SPECIFIC (progectai-* here; name varies per project).

## Hard rules
- The Jira skill PLANS; the agents BUILD; cross-repo deps wait for MERGE;
  the Jira story (via jira-ops MCP) is the durable state store.
- Never hardcode GCP project IDs (${GCP_PROJECT}) or PySpark/Airflow versions
  (confirm at runtime - migrations in flight).
- Every config change passes its domain validator before PR; two human gates
  (plan approval, per-PR CODEOWNERS merge).
- barricade-migrate / tsql-to-bq are SERVICES of the ingestion app, not skills.
