---
applyTo: "**/*.py"
---

# Python Coding Style Instructions

> Scoped to: all `*.py` files in this repo
> Extends `.github/copilot-instructions.md`

---

## 🐍 Python Version & Style

- Target **Python 3.10+**
- Follow **PEP 8** strictly — enforced via `ruff`
- Use **Black** for formatting (line length: 88)
- Use **type hints** on ALL function signatures — parameters and return types

```python
# ✅ Correct
def get_plugin_path(version: str) -> str:
    ...

# ❌ Incorrect
def get_plugin_path(version):
    ...
```

---

## 📝 Docstrings

- Use **Google-style docstrings** for all public functions, classes, and modules
- Private methods (prefixed `_`) need a one-line docstring only if non-obvious

```python
# ✅ Correct
def copy_file(self, source_uri: str, destination_uri: str) -> bool:
    """Copy a file between two GCS locations.

    Args:
        source_uri: Full GCS URI of the source file (gs://bucket/path).
        destination_uri: Full GCS URI of the destination (gs://bucket/path).

    Returns:
        True if the copy succeeded.

    Raises:
        PluginServiceError: If the GCS operation fails.
    """
```

---

## 🏗️ Class Conventions

- Use `@dataclass` for data-holding classes — do not write `__init__` manually unless logic is needed
- Operator and Sensor classes must always call `super().__init__(**kwargs)`
- Abstract base classes must use `abc.ABC` and `@abstractmethod`

---

## 🔁 Iteration & Comprehensions

- Prefer list/dict/set comprehensions over `map()` / `filter()`
- If a comprehension exceeds one logical operation, use a regular loop
- Use `enumerate()` instead of manual index tracking

```python
# ✅ Correct
active_files = [f.name for f in blobs if f.size > 0]

# ❌ Avoid
active_files = list(map(lambda f: f.name, filter(lambda f: f.size > 0, blobs)))
```

---

## ⚠️ Error Handling

- Catch **specific** exceptions — never bare `except:` or `except Exception: pass`
- Always use `raise XxxError("context") from exc` to preserve the traceback
- In `operators/` and `sensors/` — raise `AirflowException` for hard failures
- In `service/` and `utility/` — raise domain exceptions from `utility/exceptions.py`

```python
# ✅ Correct — operator layer
try:
    result = service.run(self.param)
except Exception as exc:
    raise AirflowException(f"Operator failed: {exc}") from exc

# ✅ Correct — service layer
try:
    self.client.copy_blob(...)
except google.api_core.exceptions.GoogleAPICallError as exc:
    raise PluginServiceError(f"GCS copy failed: {exc}") from exc
```

---

## 🪵 Logging

- **Operators / Sensors** → use `self.log` (Airflow's built-in task logger)
- **Service / Utility / Generator** → use `logging.getLogger(__name__)`
- Use `%s`-style lazy formatting — **not** f-strings in log calls
- **Never use `print()`** anywhere in this repo

```python
# ✅ Correct — operator/sensor
self.log.info("Processing file %s in project %s", self.file_path, self.project_id)

# ✅ Correct — service/utility
logger = logging.getLogger(__name__)
logger.info("Copying %s to %s", source_uri, destination_uri)

# ❌ Incorrect
print(f"Processing {file_path}")
logger.info(f"Copying {source_uri} to {destination_uri}")
```

---

## 🧪 Testing (pytest)

- All tests live in `airflow_plugins/unit_test/`
- is excluded from unit test runs — it requires real GCP
- Test function names: `test_<unit>_<scenario>_<expected_outcome>`
- Use `pytest-mock` (`mocker` fixture)
- **Always mock** GCS, BigQuery, Dataproc, GSM — tests must run fully offline

```python
# ✅ Correct
@pytest.mark.parametrize("version,expected", [
    ("1.0.0", "/home/airflow/gcs/plugins/airflow_platform_plugins-1.0.0-py3-none-any.whl"),
    ("2.1.3", "/home/airflow/gcs/plugins/airflow_platform_plugins-2.1.3-py3-none-any.whl"),
])
def test_plugin_selector_constructs_correct_path(version, expected):
    assert PluginSelector.build_path(version) == expected
```

---

## 📦 Imports

- Group imports: stdlib → third-party → local (separated by blank lines)
- Never use `from module import *`
- Use absolute imports throughout

```python
# ✅ Correct
import os
import logging
from typing import Any

from google.cloud import storage
from airflow.models import BaseOperator

from airflow_plugins.utility.exceptions import PluginServiceError
from airflow_plugins.service.bigquery import BigQueryService
```

---

## 🚫 Anti-Patterns — Flag Immediately

| Anti-Pattern | Severity | Layer |
|---|---|---|
| Mutable default args `def fn(x=[])` | `[BLOCKER]` | operators/sensors `__init__` |
| Bare `except:` or `except Exception: pass` | `[BLOCKER]` | all |
| `print()` anywhere in source | `[MAJOR]` | all |
| Module-level GCP client instantiation | `[BLOCKER]` | service/utility |
| `from airflow import ...` in service/utility | `[BLOCKER]` | service/utility/generator |
| `with DAG(...)` anywhere in this repo | `[BLOCKER]` | all |
| Missing type hints on public functions | `[MAJOR]` | all |
| Missing docstring on public class/method | `[MAJOR]` | all |
| f-string in logging call | `[NIT]` | all |
