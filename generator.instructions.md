---
applyTo: "airflow_plugins/generator/**/*.py"
---

# Generator Layer Instructions

> Scoped to: `airflow_plugins/generator/**/*.py`
> Covers: `conf.py`

The `generator/` package is the **config parsing and DAG construction helper layer**. It is used by `platform_dag.py` (in the DAG repo) to parse  and build the DAG structure. It bridges raw config files and the operators/sensors in this wheel.

---

## 🎯 Purpose of Each File

| File | Purpose |
|---|---|
|  | Loads and merges (DAG-level) |
|  | Typed property accessors — wraps raw config dict into structured properties |
|  | Builds the list of task definitions from parsed config |
| | Pure helper functions for config parsing (date coercion, path building, etc.) |

---

## 📋 Generator Layer Rules

### `conf.py` — Config Loader
- Must load and **merge**  — DAG-level config takes precedence over global config for overlapping keys.
- Must raise `airflowConfigError` (from ``) — not `FileNotFoundError` or `KeyError` — if required keys are missing.
- Must validate that `plugin_version` exists in `platform_conf.json` before returning — this is the contract the DAG repo depends on.
- Must not perform any GCP calls, file downloads, or network I/O — only local file reads.

```python
# ✅ Correct conf.py pattern
from airflow_plugins.utility.exceptions import airflowConfigError

class ConfigLoader:
    """Loads and merges global and DAG-level configuration.

    Args:
        conf_path: Path to conf.json.
        platform_conf_path: Path to platform_conf.json.
    """

    REQUIRED_PROPS = ("plugin_version", "dag_id", "schedule_interval")

    def __init__(self, conf_path: str, platform_conf_path: str) -> None:
        self._global = self._load_json(conf_path)
        self._platform = self._load_json(platform_conf_path)
        self._validate()

    def _validate(self) -> None:
        props = self._platform.get("props", {})
        for key in self.REQUIRED_PROPS:
            if key not in props:
                raise airflowConfigError(
                    f"Required key 'props.{key}' missing from platform_conf.json"
                )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value, with platform config taking precedence over global."""
        return self._platform.get(key, self._global.get(key, default))
```

### `props.py` — Typed Property Accessors
- Must expose typed properties — never return raw `dict` to callers.
- Must raise `airflowConfigError` with the missing key name when a required property is absent.
- Use `@property` decorators for clean access — no `get_xxx()` methods.

```python
# ✅ Correct props.py pattern
@property
def plugin_version(self) -> str:
    value = self._props.get("plugin_version")
    if not value:
        raise airflowConfigError("'plugin_version' is required but missing from props")
    return value

@property
def schedule_interval(self) -> str:
    return self._props.get("schedule_interval", "@daily")  # safe default
```

### `pipeline.py` — Task Definition Builder
- Must return a list of structured task definitions — use `@dataclass` for the task definition type.
- Must validate `task_type` against known types defined in `conf.json` templates — raise `airflowConfigError` for unknown types.
- Must not instantiate any Airflow operators — that is the DAG repo's responsibility.
- Must not make any GCP calls.

```python
# ✅ Correct — return typed task definitions, not Airflow objects
from dataclasses import dataclass

@dataclass
class TaskDefinition:
    task_id: str
    task_type: str
    params: dict[str, Any]
    depends_on: list[str]
```

### `utils.py` — Pure Helper Functions
- All functions must be **pure** — same input always gives same output, no side effects.
- No logging (pure functions don't log).
- No I/O of any kind.
- All functions must have full type hints and docstrings.

---

## 🚫 What Generator Must Never Do

- Import from `operators/`, `sensors/`, or `service/` — generator is a lower layer.
- Import from `airflow` — generator must be usable without Airflow installed.
- Make network calls, GCP calls, or read files other than the two config JSON files.
- Instantiate Airflow operators or DAG objects.

---

## 🧪 Testing Requirements for Generator

```python
# unit_test/generator/test_conf.py
import json
import pytest
from pathlib import Path
from airflow_plugins.generator.conf import ConfigLoader
from airflow_plugins.utility.exceptions import airflowConfigError


@pytest.fixture
def config_files(tmp_path):
    conf = {"gcs_bucket": "global-bucket", "project_id": "my-project"}
    platform = {
        "props": {
            "plugin_version": "1.2.0",
            "dag_id": "test_dag",
            "schedule_interval": "@daily"
        },
        "tasks": []
    }
    conf_path = tmp_path / ""
    platform_path = tmp_path / ""
    conf_path.write_text(json.dumps(conf))
    platform_path.write_text(json.dumps(platform))
    return str(conf_path), str(platform_path)


def test_config_loader_loads_successfully(config_files):
    loader = ConfigLoader(*config_files)
    assert loader.get("gcs_bucket") == "global-bucket"


def test_config_loader_raises_airflow_config_error_on_missing_plugin_version(tmp_path):
    conf_path = tmp_path / ""
    platform_path = tmp_path / ""
    conf_path.write_text("{}")
    platform_path.write_text('{"props": {"dag_id": "x", "schedule_interval": "@daily"}}')
    with pytest.raises(airflowConfigError, match="plugin_version"):
        ConfigLoader(str(conf_path), str(platform_path))


def test_platform_config_overrides_global_config(config_files, tmp_path):
    """DAG-level config must take precedence over global config on key collision."""
    conf_path, platform_path = config_files
    # Modify platform to override gcs_bucket
    import json
    data = json.loads(Path(platform_path).read_text())
    data["gcs_bucket"] = "dag-specific-bucket"
    Path(platform_path).write_text(json.dumps(data))

    loader = ConfigLoader(conf_path, platform_path)
    assert loader.get("gcs_bucket") == "dag-specific-bucket"
```
