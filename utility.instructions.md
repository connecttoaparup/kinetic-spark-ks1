---
applyTo: "airflow_plugins/utility/**/*.py,airflow_plugins/utility/**/*.yaml"
---

# Utility Layer Instructions

> Scoped to: `airflow_plugins/utility/**/*.py`, `airflow_plugins/utility/**/*.yaml`
> Covers:
> - `utility/` — YAML schema validation subsystem
> - `utility/secrets/` — Secret Manager client abstraction
> - `utility/*.py` — Pure helper scripts (data_mask, data_read, data_write, exceptions, gcs_client_singleton, email_sender, file_checksum, pager_duty, py_query, etc.)

The `utility/` layer is the **foundation of the entire wheel**. It is imported by `service/`, `operators/`, and `sensors/`. It must have **zero Airflow dependencies**, be independently testable, and have no side effects at import time.

---

## ⚠️ Absolute Rule: No Airflow Imports

```python
# ❌ Forbidden anywhere in utility/
from airflow import AirflowException
from airflow.models import Variable
from airflow.hooks.base import BaseHook
```

If Airflow is imported in `utility/`, it breaks all non-Airflow usage of the wheel and makes unit testing without Airflow impossible.

---

## 📋 Sub-Package Rules

---

### `utility/exceptions.py` — Domain Exception Hierarchy

- All custom exceptions in this repo must subclass from exceptions defined here.
- Never raise raw `Exception` — always use a named domain exception.
- Exceptions must carry enough context to diagnose without reading source code.

```python
# ✅ Correct hierarchy
class airflowBaseError(Exception):
    """Base exception for all airflow plugin errors."""

class airflowServiceError(airflowBaseError):
    """Raised when a GCP service operation fails."""

class airflowConfigError(airflowBaseError):
    """Raised when configuration is invalid or missing."""

class airflowSecretError(airflowBaseError):
    """Raised when secret retrieval fails."""

class airflowValidationError(airflowBaseError):
    """Raised when config schema validation fails."""
```

---

### `utility/` — GCS Client Singleton

- Must implement a **module-level singleton** so the GCS client is created once per Python process.
- Must accept `project` as a parameter — never use ADC project default.
- Must be thread-safe if Airflow is running in multi-threaded mode.

```python
# ✅ Correct singleton pattern
from __future__ import annotations
from google.cloud import storage

_gcs_client: storage.Client | None = None


def get_gcs_client(project: str) -> storage.Client:
    """Return a shared GCS client, creating it on first call.

    Args:
        project: GCP project ID.

    Returns:
        A configured `google.cloud.storage.Client` instance.
    """
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client(project=project)
    return _gcs_client


def reset_gcs_client() -> None:
    """Reset the singleton (for use in tests only)."""
    global _gcs_client
    _gcs_client = None
```

---

### `utility/` — Data Masking

- All functions must return a **new masked string** — never mutate the original.
- Masking must be applied before any logging of values that could be secrets, PII, or credentials.
- Must support: full mask, partial mask (show last N chars), key-value pair masking in dicts/strings.

```python
# ✅ Usage pattern (called from service/ before logging)
from airflow_plugins.utility.data_mask import mask_value

logger.info("Using token: %s", mask_value(token, show_last=4))
# Output: "Using token: ****abcd"
```

---

### `utility/secrets/` — Secret Manager Abstraction

#### `core`
- Must define an **abstract base class** with `get_secret(secret_id: str) -> str`.
- All concrete client implementations must subclass this interface.
- This enables test mocking without any GSM dependency.

```python
from abc import ABC, abstractmethod

class SecretClientInterface(ABC):
    """Abstract interface for secret retrieval."""

    @abstractmethod
    def get_secret(self, secret_id: str) -> str:
        """Retrieve a secret value by ID.

        Args:
            secret_id: The secret's resource name or short ID.

        Returns:
            The secret value as a string.

        Raises:
            airflowSecretError: If the secret cannot be retrieved.
        """
```

#### `clients/`
- Must implement `SecretClientInterface`.
- Must never cache secret values in memory beyond the duration of a single call — secrets rotate.
- Must raise `airflowSecretError` (from `utility/exceptions.py`) on any GSM failure.
- Must never log the secret value — only log the secret ID.

```python
# ✅ Correct GSM client
class GSMClient(SecretClientInterface):
    def get_secret(self, secret_id: str) -> str:
        logger.info("Fetching secret: %s", secret_id)  # log ID only, never value
        try:
            response = self._sm_client.access_secret_version(name=secret_id)
            return response.payload.data.decode("utf-8")
        except google.api_core.exceptions.GoogleAPICallError as exc:
            raise airflowSecretError(f"Failed to retrieve secret {secret_id}") from exc
```

---

### `utility//` — Config Validation Subsystem

#### ``
- Must validate against YAML schemas defined in `job.yaml`, `services.yaml`, `task.yaml`.
- Must raise `airflowValidationError` (not `airflowConfigError`) on schema violations.
- Must return a **typed, coerced config object** — never return raw dict from validation.
- Must call `coercer_functions.py` for type coercion before validation.

#### ``
- Rules must be data-driven (loaded from YAML) — do not hardcode field names in Python.
- Each rule must have: field name, required/optional, type, allowed values (if enumerated).

#### ``
- All coercer functions must be **pure functions** — no side effects, no I/O.
- Must handle `None` input gracefully — return `None` or a documented default.
- Type signatures must be explicit: `def coerce_to_int(value: Any) -> int | None`.

#### ``
- Config exceptions must include the **field name** and **invalid value** in the message.
- Never expose full config payloads in exception messages — they may contain secrets.

#### YAML Schema Files (`job.yaml`, `services.yaml`, `task.yaml`)
- Field additions are backward compatible — always optional with a documented default.
- Field removals or type changes require a version comment and a `CHANGELOG.md` entry.
- Every field must have an inline comment explaining its purpose and allowed values.

```yaml
# ✅ Correct YAML field definition
fields:
  plugin_version:
    type: string
    required: true
    description: "Semantic version of the wheel file (e.g., 1.2.0)"
    pattern: "^\\d+\\.\\d+\\.\\d+$"
```

---

### General `utility/*.py` Helper Scripts

Rules for `data_read.py`, `data_write.py`, `file_checksum.py`, `py_query.py`, `arg_parser_utility.py`, `config_yaml_read.py`, `email_sender.py`, `pager_duty.py`, `generate_html_template.py`:

- All functions must be **pure or clearly documented as having side effects**.
- Functions with side effects (file I/O, network, email send) must have the side effect named in the function name or clearly documented: `send_email()`, `write_to_gcs()`, not `process()`.
- No global mutable state — use parameters, not module-level variables that accumulate state.
- All file I/O must use context managers (`with open(...) as f`).
- `config_yaml_read.py` must validate that the file exists and is valid YAML before returning — raise `airflowConfigError` on failure, not `FileNotFoundError` directly.

---

## 🧪 Testing Requirements for Utility

- `utility/` must have the **highest test coverage in the repo** — it is the foundation everything depends on.
- Every function in `utility/` must have tests covering: happy path, invalid input, and boundary values.
- `utility/secrets/` tests must always mock the GSM client — never call real Secret Manager.
- `utility/config_validator/` tests must cover: valid config, missing required field, wrong type, unknown field.

```python
# unit_test/utility/test_data_mask.py
def test_mask_value_hides_all_but_last_four_chars():
    assert mask_value("super_secret_token", show_last=4) == "**************oken"

def test_mask_value_with_none_returns_empty_mask():
    assert mask_value(None) == "****"

def test_mask_value_shorter_than_show_last_fully_masked():
    assert mask_value("abc", show_last=4) == "****"
```

```python
# unit_test/utility/test_gcs_client_singleton.py
from airflow_plugins.utility.gcs_client_singleton import get_gcs_client, reset_gcs_client

def test_get_gcs_client_returns_same_instance_on_repeated_calls(mocker):
    mocker.patch("google.cloud.storage.Client", autospec=True)
    reset_gcs_client()
    client_a = get_gcs_client("project-a")
    client_b = get_gcs_client("project-a")
    assert client_a is client_b  # singleton — must be the exact same object

def test_reset_gcs_client_allows_new_instance(mocker):
    mocker.patch("google.cloud.storage.Client", autospec=True)
    reset_gcs_client()
    client_a = get_gcs_client("project-a")
    reset_gcs_client()
    client_b = get_gcs_client("project-a")
    assert client_a is not client_b
```
