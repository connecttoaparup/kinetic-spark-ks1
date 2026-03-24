---
applyTo: "airflow_plugins/operators/**/*.py,airflow_plugins/controller/operators.py"
---

# Operators Layer Instructions

> Scoped to: `airflow_plugins/operators/**/*.py`, `airflow_plugins/controller/operators.py`

Operators are the **public API of this wheel**. Every class and method here is a contract that DAGs across the organisation depend on. Treat every change as a public API change.

---

## ✅ Mandatory Structure for Every Operator

Every operator must follow this exact structure — no exceptions:

```python
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Sequence

from airflow.models import BaseOperator
from airflow.exceptions import AirflowException

from airflow_plugins.service.<module> import <ServiceClass>

if TYPE_CHECKING:
    from airflow.utils.context import Context

logger = logging.getLogger(__name__)


class MyairflowOperator(BaseOperator):
    """One-line summary of what this operator does.

    Called from DAGs to <describe the task purpose>.
    Delegates business logic to `airflow_plugins.service.<module>`.

    Args:
        param_one: Description of param_one.
        param_two: Description of param_two. Defaults to None.
        gcp_project_id: GCP project to run operations against.

    Example:
        MyairflowOperator(
            task_id="my_task",
            param_one="value",
            gcp_project_id="{{ var.value.gcp_project }}",
        )
    """

    # Declare ALL template fields — any param that accepts Jinja2 must be listed here
    template_fields: Sequence[str] = ("param_one", "gcp_project_id")

    def __init__(
        self,
        *,
        param_one: str,
        gcp_project_id: str,
        param_two: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.param_one = param_one
        self.gcp_project_id = gcp_project_id
        self.param_two = param_two

    def execute(self, context: Context) -> Any:
        """Execute the operator task.

        Args:
            context: Airflow task execution context.

        Returns:
            Result value pushed to XCom (or None).

        Raises:
            AirflowException: If the operation fails.
        """
        self.log.info(
            "Starting %s for project=%s", self.__class__.__name__, self.gcp_project_id
        )
        try:
            service = <ServiceClass>(project_id=self.gcp_project_id)
            result = service.run(self.param_one, self.param_two)
            self.log.info("Completed successfully: %s", result)
            return result
        except Exception as exc:
            raise AirflowException(
                f"{self.__class__.__name__} failed: {exc}"
            ) from exc
```

---

## 📋 Operator Rules

### `__init__` Rules
- Always call `super().__init__(**kwargs)` — passing `**kwargs` is mandatory so Airflow's base params (retries, timeout, etc.) work.
- Use keyword-only args (`*` before params) — prevents positional arg mistakes in DAG calls.
- All params must have type hints.
- New **optional** params must have a default value — adding a required param to an **existing** operator is a `[BLOCKER]`.
- Store all params as `self.<param>` in `__init__` — never compute state in `__init__`.

### `execute()` Rules
- Must be defined on every operator — a missing `execute()` is a `[BLOCKER]`.
- Must accept `context: Context` — use `TYPE_CHECKING` import to avoid runtime overhead.
- Must use `self.log` — never `print()` or module-level `logging`.
- Must **not** contain business logic — delegate to `service/` layer.
- Must wrap all logic in try/except and raise `AirflowException` on failure.
- Return value is pushed to XCom automatically — document it in the docstring.

### `template_fields` Rules
- Must declare every param that DAGs will template with Jinja2 (e.g., `{{ ds }}`, `{{ var.value.x }}`).
- Common fields that almost always need templating: `gcp_project_id`, file paths, dataset names, dates.
- Missing `template_fields` means DAG authors cannot use Jinja in that param — flag as `[MAJOR]`.

### No Business Logic in Operators
- Operators must only: validate inputs, instantiate service, call service method, log result.
- GCS/BigQuery/Dataproc API calls belong in `service/` — not here.
- If business logic appears directly in `execute()`, flag as `[MAJOR]`.

---

## 🚫 Backward Compatibility Rules (Operators)

These are the most critical rules in this entire repo:

| Change Type | Severity | Action Required |
|---|---|---|
| Removing an existing operator class | `[BLOCKER]` | Never — deprecate first |
| Renaming an operator class | `[BLOCKER]` | Never — add alias + deprecation warning |
| Removing a param from `__init__` | `[BLOCKER]` | Never — mark deprecated, keep accepting it |
| Adding a required param to existing operator | `[BLOCKER]` | Must be optional with a default |
| Changing a param's type (e.g. `str` → `list`) | `[BLOCKER]` | Breaking — needs MAJOR version bump |
| Removing a field from `template_fields` | `[MAJOR]` | Breaks DAGs using Jinja on that field |
| Changing `execute()` return type | `[MAJOR]` | Breaks DAGs reading XCom from this task |

### Deprecation Pattern (use when retiring a param)
```python
import warnings

def __init__(self, *, old_param: str | None = None, new_param: str = "", **kwargs):
    super().__init__(**kwargs)
    if old_param is not None:
        warnings.warn(
            "'old_param' is deprecated and will be removed in v3.0.0. "
            "Use 'new_param' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        new_param = old_param  # migrate value transparently
    self.new_param = new_param
```

---

## 🧪 Testing Requirements for Operators

Every operator must have a test file at `unit_test/operators/test_<operator_file>.py`:

```python
# unit_test/operators/test_my_airflow_operator.py
from unittest.mock import MagicMock, patch
import pytest
from airflow.exceptions import AirflowException

from airflow_plugins.operators.my_operator import MyairflowOperator


@pytest.fixture
def operator():
    return MyairflowOperator(
        task_id="test_task",
        param_one="test_value",
        gcp_project_id="test-project",
    )


def test_execute_calls_service_with_correct_params(operator):
    """execute() must delegate to the service layer with correct params."""
    mock_context = MagicMock()
    with patch("airflow_plugins.operators.my_operator.ServiceClass") as mock_service_cls:
        mock_service = mock_service_cls.return_value
        mock_service.run.return_value = "ok"
        result = operator.execute(mock_context)
        mock_service_cls.assert_called_once_with(project_id="test-project")
        mock_service.run.assert_called_once_with("test_value", None)
        assert result == "ok"


def test_execute_raises_airflow_exception_on_service_failure(operator):
    """execute() must wrap service errors in AirflowException."""
    mock_context = MagicMock()
    with patch("airflow_plugins.operators.my_operator.ServiceClass") as mock_service_cls:
        mock_service_cls.return_value.run.side_effect = RuntimeError("GCP error")
        with pytest.raises(AirflowException, match="failed"):
            operator.execute(mock_context)


def test_template_fields_contains_expected_fields(operator):
    """template_fields must include all Jinja-templatable params."""
    assert "param_one" in operator.template_fields
    assert "gcp_project_id" in operator.template_fields


def test_adding_optional_param_does_not_break_existing_call():
    """Existing instantiation without new optional params must still work."""
    op = MyairflowOperator(task_id="t", param_one="v", gcp_project_id="p")
    assert op.param_two is None  # default must be preserved
```

---

## 🔢 When to Bump the Wheel Version

| Change | Version Bump |
|---|---|
| New operator class added | `MINOR` (e.g. `1.1.0 → 1.2.0`) |
| Existing operator modified (backward compatible) | `PATCH` (e.g. `1.1.0 → 1.1.1`) |
| Any breaking change (param removed/renamed/type changed) | `MAJOR` (e.g. `1.1.0 → 2.0.0`) |

Always update `CHANGELOG.md` with the change description and affected operators.
