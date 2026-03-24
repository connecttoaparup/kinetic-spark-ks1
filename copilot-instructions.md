# Copilot Instructions — `airflow_plugins` Wheel Source Repo

## 🎯 What This Repo Is

This is the **source package for the airflow Ingestion Framework**:
`airflow_platform_plugins-{version}-py3-none-any.whl`

Every operator, sensor, service, and utility in this repo is consumed by **production DAGs across the organisation** via that wheel file. A broken interface, unchecked GCP call, or silent exception **will fail DAGs across multiple teams without warning**.

**There are NO DAG files here. Copilot must never suggest `with DAG(...)`, `DAG()` instantiation, or Airflow scheduler constructs in this repo.**

---

## 📁 Actual Repository Structure

```
airflow_plugins/
├── controller/            ← Thin routing layer; delegates to operators/sensors
│   ├── operators.py
│   └── sensors.py
├── generator/             ← DAG-side config parsing: conf, pipeline, props, utils
│   ├── conf.py
│   ├── pipeline.py
│   ├── props.py
│   └── utils.py
├── operators/             ← BaseOperator subclasses (Dataproc, variable, config validator)
│   ├── config.py
│   ├── dataproc.py
│   ├── dataproc_serverless.py
│   ├── airflow_ingestion_app_config_validator_operator.py
│   └── variable.py
├── sensors/               ← BaseSensorOperator subclasses (GCS, external run ID, time range)
│   ├── airflow_gcs_file_sensor.py
│   ├── external_run_id_sensor.py
│   ├── storage.py
│   └── time_range_external_task_sensor.py
├── service/               ← Business logic services called by operators (GCS, BQ, Dataproc, email...)
│   ├── bigquery.py
│   ├── dataproc.py
│   ├── airflow_gcs_file_backup.py
│   ├── airflow_gcs_file_converter.py
│   ├── airflow_gcs_file_copy_move.py
│   ├── airflow_gcs_file_meta_report.py
│   ├── airflow_gcs_file_rename.py
│   ├── flow.py
│   ├── gcs_file_merge.py
│   ├── gcs_to_s3_file_transfer.py
│   └── ...  (all GCS/BQ/Dataproc/REST service scripts)
├── utility/               ← Pure helpers (no Airflow imports allowed here)
│   ├── config_validator/  ← YAML-schema based config validation subsystem
│   │   ├── config_validator.py
│   │   ├── config_checker_rules.py
│   │   ├── coercer_functions.py
│   │   ├── custom_config_exception.py
│   │   ├── secret_validator_helper.py
│   │   ├── job.yaml
│   │   ├── services.yaml
│   │   └── task.yaml
│   ├── secrets/           ← Secret client abstraction (GSM)
│   │   ├── clients/gsm_client.py
│   │   └── core/secret_client_interface.py
│   ├── data_mask.py
│   ├── data_read.py / data_write.py
│   ├── exceptions.py
│   ├── gcs_client_singleton.py
│   └── ...
└── unit_test/
    └── gsm_e2e.py
```

---

## 🔑 Layer Responsibilities — Copilot Must Enforce These Boundaries

| Layer | Responsibility | May import from | Must NOT import |
|---|---|---|---|
| `operators/` | Airflow task entrypoints only; no business logic | `service/`, `utility/`, `generator/` | Other `operators/` directly |
| `sensors/` | Airflow poke/sensor logic only | `service/`, `utility/` | `operators/` |
| `controller/` | Routes calls to correct operator/sensor | `operators/`, `sensors/` | `service/` directly |
| `generator/` | Parses configs for DAG construction | `utility/` | `operators/`, `sensors/`, `service/` |
| `service/` | All GCP/REST/business logic | `utility/` | `operators/`, `sensors/`, `generator/` |
| `utility/` | Pure helpers, no side effects | stdlib, GCP clients only | `operators/`, `sensors/`, `service/`, `generator/` |

---

## ⚠️ Cross-Cutting Rules (All Files)

### Backward Compatibility — Highest Priority
- **Never remove or rename a public method, class, or parameter** without a deprecation cycle.
- **Never change the type or meaning of an existing parameter** — this silently breaks DAGs.
- Adding a new **optional** parameter with a default value is allowed.
- Adding a new **required** parameter to an existing operator/sensor is a `[BLOCKER]` — it breaks all existing DAG calls immediately.
- Any breaking change requires a **MAJOR version bump** in `pyproject.toml` and a `CHANGELOG.md` entry.

### GCP Client Usage
- GCP clients (`bigquery.Client`, `storage.Client`, `dataproc_v1`) must **never** be instantiated at module level.
- Always instantiate inside methods or use the singleton pattern (`utility/gcs_client_singleton.py`).
- Always pass explicit `project` and credential parameters — never rely on ADC defaults silently.
- Always set timeouts on GCP API calls.

### Error Handling
- All GCP calls must catch `google.api_core.exceptions.GoogleAPICallError` and re-raise with context.
- Never silently swallow exceptions — Airflow must see task failures to retry and alert correctly.
- Use `AirflowException` for hard failures, `AirflowSkipException` for intentional skips.

### Logging
- In `operators/` and `sensors/`: use `self.log` (Airflow's built-in task logger).
- In `service/` and `utility/`: use `logging.getLogger(__name__)`.
- **Never use `print()`** anywhere in this repo.

### Secrets
- All secret access must go through `utility/secrets/` — never call GSM or Secret Manager directly from operators or services.
- Never log secret values — always mask using `utility/data_mask.py`.

### No DAG Constructs — ABSOLUTE RULE
- `from airflow.models import DAG`, `with DAG(...)`, `DAG()` must **never** appear in any file in this repo.
- Flag as `[BLOCKER]` immediately if seen.

---

## 🤖 Copilot: Which Instruction File to Apply

| File being changed | Apply this instruction file |
|---|---|
| `operators/*.py` | `.github/instructions/operators.instructions.md` |
| `sensors/*.py` | `.github/instructions/sensors.instructions.md` |
| `controller/*.py` | `.github/instructions/operators.instructions.md` + `sensors.instructions.md` |
| `service/*.py` | `.github/instructions/service.instructions.md` |
| `utility/**/*.py` | `.github/instructions/utility.instructions.md` |
| `generator/*.py` | `.github/instructions/generator.instructions.md` |
