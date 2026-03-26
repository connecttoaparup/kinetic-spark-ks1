# Changelog — `airflow_platform_plugins`

All notable changes to this wheel package are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Version Bump Rules

| Change type | Version bump | Example |
|---|---|---|
| New operator or sensor added | `MINOR` | `1.0.0 → 1.1.0` |
| Existing operator/sensor modified (backward compatible) | `PATCH` | `1.0.0 → 1.0.1` |
| Bug fix in service or utility | `PATCH` | `1.0.0 → 1.0.1` |
| Breaking change (param removed/renamed/type changed) | `MAJOR` | `1.0.0 → 2.0.0` |
| New service or utility script added | `MINOR` | `1.0.0 → 1.1.0` |

> ⚠️ Before releasing any version — run all 14 gates:
> `python scripts/pre_review_gate.py`

---

## [Unreleased]

> Move items here while working on the next version.
> Promote to a versioned section when the wheel is built and uploaded to GCS.

### Added
-

### Changed
-

### Fixed
-

### Deprecated
-

### Removed
-

### Security
-

---

## [1.0.0] — YYYY-MM-DD

> 🎉 Initial release of the `airflow_platform_plugins` wheel.

### Added

#### Operators (`airflow_plugins/operators/`)
- `DataprocOperator` — submits Dataproc Spark jobs from DAG tasks
- `DataprocServerlessOperator` — submits serverless Dataproc batch jobs
- `VariableOperator` — reads and sets Airflow Variables from config
- `ConfigValidatorOperator` (`AIRFLOW_ingestion_app_config_validator_operator.py`) — validates DAG config against YAML schema before pipeline runs

#### Sensors (`airflow_plugins/sensors/`)
- `GCSFileSensor` (`airflow_gcs_file_sensor.py`) — polls GCS for file existence with configurable prefix and count
- `ExternalRunIdSensor` — waits for an external pipeline run ID to complete
- `StorageSensor` — generic GCS storage availability sensor
- `TimeRangeExternalTaskSensor` — waits for an external task within a configurable time window

#### Services (`airflow_plugins/service/`)
- `bigquery.py` — BigQuery job execution, query management, table operations
- `dataproc.py` — Dataproc cluster job submission and status polling
- `airflow_gcs_file_backup.py` — GCS file backup with timestamp versioning
- `airflow_gcs_file_converter.py` — GCS file format conversion utilities
- `airflow_gcs_file_copy_move.py` — GCS file copy and move operations
- `airflow_gcs_file_meta_report.py` — GCS file metadata reporting
- `airflow_gcs_file_rename.py` — GCS file rename with pattern support
- `flow.py` — Pipeline flow control utilities
- `gcs_file_merge.py` — Merges multiple GCS files into one
- `gcs_to_s3_file_transfer.py` — Cross-cloud GCS to S3 file transfer
- `file_download_rest_api.py` — Downloads files from REST API endpoints to GCS
- `json_rest_api_extractor.py` — Extracts and transforms JSON from REST APIs
- `generate_sql_from_jsonl.py` — Generates SQL from JSONL schema definitions
- `tableau_refresh_report.py` — Triggers Tableau report refresh via API
- `airflow_auto_email_service.py` — Automated email notifications for pipeline events
- `airflow_mf_email_service.py` — MF-specific email notification service
- `set_lastdate_update.py` — Updates last-processed-date markers
- `env.py` — Environment configuration resolution
- `properties.py` — Shared pipeline property accessors
- `task.py` — Task-level utility functions
- `utils.py` — General service utilities
- `validate.py` — Input validation helpers
- `variables.py` — Airflow Variable management
- `wait_dummy_op.py` — No-op wait operator for pipeline gating

#### Utility (`airflow_plugins/utility/`)
- `config_validator/` — YAML schema validation subsystem
  - `config_validator.py` — validates configs against `job.yaml`, `services.yaml`, `task.yaml`
  - `config_checker_rules.py` — data-driven validation rules
  - `coercer_functions.py` — type coercion functions
  - `custom_config_exception.py` — validation exception with field context
  - `secret_validator_helper.py` — validates secret references in config
- `secrets/` — Secret Manager abstraction
  - `core/secret_client_interface.py` — abstract `SecretClientInterface`
  - `clients/gsm_client.py` — Google Secret Manager implementation
- `arg_parser_utility.py` — CLI argument parsing helpers
- `config_yaml_read.py` — YAML config file reader with validation
- `data_mask.py` — Masks sensitive values before logging
- `data_read.py` — Data read utilities (GCS, local)
- `data_write.py` — Data write utilities (GCS, local)
- `email_sender.py` — Low-level email sending utility
- `exceptions.py` — Domain exception hierarchy (`PluginServiceError`, `PluginConfigError`, etc.)
- `file_checksum.py` — File integrity checksum generation and verification
- `gcs_client_singleton.py` — Shared GCS client singleton
- `generate_html_template.py` — HTML email template generator
- `pager_duty.py` — PagerDuty alert integration
- `py_query.py` — Python-based query execution helpers

#### Generator (`airflow_plugins/generator/`)
- `conf.py` — Merges `conf.json` and `platform_conf.json`
- `pipeline.py` — Builds typed task definition list from config
- `props.py` — Typed property accessors for DAG config
- `utils.py` — Pure config parsing helper functions

#### Controller (`airflow_plugins/controller/`)
- `operators.py` — Routes DAG operator calls to correct operator class
- `sensors.py` — Routes DAG sensor calls to correct sensor class

#### Infrastructure
- `scripts/pre_review_gate.py` — 14-gate pre-PR quality gate script
- `pyproject.toml` — Wheel build config with Black, Ruff, Mypy, Pylint, Pytest settings
- `.github/copilot-instructions.md` — Repo-wide Copilot rules
- `.github/instructions/` — Layer-scoped Copilot instruction files

### Wheel
- Built: `airflow_platform_plugins-1.0.0-py3-none-any.whl`
- Uploaded: `gs://<composer-bucket>/plugins/`
- Requires: Python 3.10+, Apache Airflow 2.7+

---

## Release Checklist

> Copy this checklist into your PR description for every release.

```
## Release Checklist — airflow_platform_plugins vX.Y.Z

### Developer (before raising PR)
- [ ] All 14 gates passed: `python scripts/pre_review_gate.py`
- [ ] Version bumped in setup.py (MAJOR / MINOR / PATCH)
- [ ] CHANGELOG.md updated — [Unreleased] promoted to [X.Y.Z] with today's date
- [ ] Wheel built locally: `python -m build`
- [ ] Wheel tested locally against a DAG
- [ ] plugin_version updated in DAG repo platform_conf.json
- [ ] Breaking changes documented with migration notes (if MAJOR bump)
- [ ] Deprecated params use the deprecation warning pattern

### After PR is merged — SRE CI/CD handles automatically
- [ ] Final wheel built from setup.py version
- [ ] Wheel uploaded to GCS: gs://<composer-bucket>/plugins/
```
