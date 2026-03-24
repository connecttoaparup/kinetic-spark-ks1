---
applyTo: "airflow_plugins/sensors/**/*.py,airflow_plugins/controller/sensors.py"
---

# Sensors Layer Instructions

> Scoped to: `airflow_plugins/sensors/**/*.py`, `airflow_plugins/controller/sensors.py`
> Covers: `airflow_gcs_file_sensor.py`, `external_run_id_sensor.py`, `storage.py`, `external_task_sensor.py`

Sensors are **long-running polling operators**. Incorrect implementation causes Airflow worker slot exhaustion, hung DAGs, and scheduler pressure across all teams. Every sensor in this repo must be efficient, safe to reschedule, and clearly bounded.

---

## ✅ Mandatory Structure for Every Sensor

```python
from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, Sequence

from airflow.sensors.base import BaseSensorOperator
from airflow.exceptions import AirflowException, AirflowSkipException

from airflow_plugins.service.<module> import <ServiceClass>

if TYPE_CHECKING:
    from airflow.utils.context import Context


class MyairflowSensor(BaseSensorOperator):
    """One-line summary of what this sensor polls for.

    Polls <resource> until <condition> is met.
    Uses reschedule mode by default to avoid blocking a worker slot.

    Args:
        resource_path: GCS path / resource identifier to monitor.
        gcp_project_id: GCP project to query against.
        expected_count: Number of files/records expected. Defaults to 1.

    Example:
        MyairflowSensor(
            task_id="wait_for_file",
            resource_path="gs://my-bucket/data/{{ ds }}/",
            gcp_project_id="{{ var.value.gcp_project }}",
            mode="reschedule",
            timeout=3600,
            poke_interval=60,
        )
    """

    template_fields: Sequence[str] = ("resource_path", "gcp_project_id")

    def __init__(
        self,
        *,
        resource_path: str,
        gcp_project_id: str,
        expected_count: int = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.resource_path = resource_path
        self.gcp_project_id = gcp_project_id
        self.expected_count = expected_count

    def poke(self, context: Context) -> bool:
        """Check whether the condition is met.

        Args:
            context: Airflow task execution context.

        Returns:
            True if condition is met (sensor succeeds), False to keep polling.

        Raises:
            AirflowSkipException: If the resource is confirmed absent and skip is preferred.
            AirflowException: If a non-recoverable error occurs during polling.
        """
        self.log.info("Poking for resource: %s", self.resource_path)
        try:
            service = <ServiceClass>(project_id=self.gcp_project_id)
            count = service.check(self.resource_path)
            self.log.info("Found %d / %d expected", count, self.expected_count)
            return count >= self.expected_count
        except <RecoverableError>:
            self.log.warning("Transient error during poke — will retry", exc_info=True)
            return False
        except Exception as exc:
            raise AirflowException(
                f"{self.__class__.__name__} failed permanently: {exc}"
            ) from exc
```

---

## 📋 Sensor-Specific Rules

### `poke()` Rules
- Must return `bool` — `True` = condition met, `False` = keep polling.
- Must **never block** on long I/O — use service layer with timeouts.
- Must distinguish between **transient errors** (return `False`, log warning) and **permanent errors** (raise `AirflowException`).
- Use `AirflowSkipException` when the resource is confirmed absent and skipping downstream is the right behaviour.
- Must use `self.log` — never `print()`.

### Reschedule Mode — Mandatory Default
- All sensors in this repo must default to `mode="reschedule"` unless there is an explicit documented reason for `mode="poke"`.
- `mode="poke"` holds a worker slot for the entire polling duration — in a shared Composer environment this starves other teams' DAGs.
- If a sensor PR uses `mode="poke"` without a comment, flag as `[MAJOR]`.

```python
# ✅ Always set these sensible defaults in __init__
def __init__(self, *, ..., **kwargs):
    kwargs.setdefault("mode", "reschedule")
    kwargs.setdefault("poke_interval", 60)   # seconds
    kwargs.setdefault("timeout", 3600)        # 1 hour max
    super().__init__(**kwargs)
```

### Timeout Rules
- Every sensor must have a bounded `timeout` — an infinite sensor will hang a DAG forever.
- Default timeout must be set in `__init__` via `kwargs.setdefault("timeout", <seconds>)`.
- Timeout value must be documented in the class docstring.

### GCP Polling Efficiency
- Never call GCP list APIs (e.g., `list_blobs`) without a prefix filter — unbounded GCS listing causes quota exhaustion.
- Cache nothing between poke calls — each `poke()` is stateless.
- Keep `poke_interval` at minimum 30 seconds for GCS/BQ sensors — polling faster than this rarely helps and increases API quota usage.

---

## 🚫 Backward Compatibility (Sensors)

Same rules as operators — sensors are also part of the public wheel API:

| Change | Severity |
|---|---|
| Removing sensor class | `[BLOCKER]` |
| Adding required `__init__` param | `[BLOCKER]` |
| Changing `poke()` return from `bool` to anything else | `[BLOCKER]` |
| Changing default `mode` from `reschedule` to `poke` | `[MAJOR]` |
| Removing a `template_fields` entry | `[MAJOR]` |

---

## 🧪 Testing Requirements for Sensors

```python
# unit_test/sensors/test_my_airflow_sensor.py
from unittest.mock import MagicMock, patch
import pytest
from airflow.exceptions import AirflowException, AirflowSkipException

from airflow_plugins.sensors.my_sensor import MyairflowSensor


@pytest.fixture
def sensor():
    return MyairflowSensor(
        task_id="test_sensor",
        resource_path="gs://bucket/path/",
        gcp_project_id="test-project",
    )


def test_poke_returns_false_when_condition_not_met(sensor):
    mock_context = MagicMock()
    with patch("airflow_plugins.sensors.my_sensor.ServiceClass") as mock_svc:
        mock_svc.return_value.check.return_value = 0
        assert sensor.poke(mock_context) is False


def test_poke_returns_true_when_condition_met(sensor):
    mock_context = MagicMock()
    with patch("airflow_plugins.sensors.my_sensor.ServiceClass") as mock_svc:
        mock_svc.return_value.check.return_value = 1
        assert sensor.poke(mock_context) is True


def test_poke_raises_airflow_exception_on_permanent_error(sensor):
    mock_context = MagicMock()
    with patch("airflow_plugins.sensors.my_sensor.ServiceClass") as mock_svc:
        mock_svc.return_value.check.side_effect = PermissionError("Access denied")
        with pytest.raises(AirflowException):
            sensor.poke(mock_context)


def test_default_mode_is_reschedule(sensor):
    assert sensor.mode == "reschedule"


def test_default_timeout_is_bounded(sensor):
    assert sensor.timeout is not None
    assert sensor.timeout <= 86400  # max 24 hours
```
