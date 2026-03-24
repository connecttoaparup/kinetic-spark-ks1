---
applyTo: "**"
---

# PR Review Checklist — Copilot Code Review Instructions

> Scoped to: all files in this repository
> Copilot Code Review must apply this checklist to every pull request
> before a human reviewer is assigned.

---

## 🔢 Severity Labels

| Label | Meaning | Must resolve before merge? |
|---|---|---|
| `[BLOCKER]` | Correctness, security, or breaks production DAGs | ✅ Yes |
| `[MAJOR]` | Missing tests, broken conventions, significant risk | ✅ Yes |
| `[MINOR]` | Style, naming, readability | ⚠️ Recommended |
| `[NIT]` | Optional improvement | ❌ Author's discretion |

---

## ✅ Review Checklist

### 1. PR Hygiene
- [ ] PR title format: `<type>(<scope>): <short description>` e.g. `feat(operators): add BigQuery export operator`
- [ ] PR description explains **what** changed and **why** — not just which files
- [ ] PR is scoped to a single concern — flag mixed changes `[MAJOR]`
- [ ] `CHANGELOG.md` is updated with the change and affected layer
- [ ] `pyproject.toml` version is bumped correctly (MAJOR/MINOR/PATCH)

### 2. Wheel Versioning
- [ ] New operator or sensor added → `MINOR` bump `[MAJOR]`
- [ ] Existing operator/sensor modified (backward compatible) → `PATCH` bump `[MAJOR]`
- [ ] Any breaking change → `MAJOR` bump `[BLOCKER]`
- [ ] New wheel version exists in GCS before PR is merged `[BLOCKER]`

### 3. Backward Compatibility
- [ ] No existing operator/sensor class removed or renamed `[BLOCKER]`
- [ ] No existing `__init__` parameter removed or renamed `[BLOCKER]`
- [ ] No new **required** parameter added to existing operator/sensor `[BLOCKER]`
- [ ] No change to `execute()` return type that breaks XCom readers `[MAJOR]`
- [ ] No field removed from `template_fields` `[MAJOR]`
- [ ] Deprecated params use the deprecation warning pattern `[MAJOR]`

### 4. No DAG Constructs
- [ ] No `with DAG(...)` anywhere in this repo `[BLOCKER]`
- [ ] No `from airflow.models import DAG` anywhere `[BLOCKER]`
- [ ] No Airflow scheduler constructs (`schedule_interval`, `catchup`, `start_date` as DAG params) `[BLOCKER]`

### 5. Layer Boundary Violations
- [ ] `service/` has no `from airflow` imports `[BLOCKER]`
- [ ] `utility/` has no `from airflow` imports `[BLOCKER]`
- [ ] `generator/` has no `from airflow` imports `[BLOCKER]`
- [ ] `operators/` does not contain business/GCP logic — delegates to `service/` `[MAJOR]`
- [ ] `sensors/` does not contain business/GCP logic — delegates to `service/` `[MAJOR]`
- [ ] `utility/` does not import from `service/`, `operators/`, or `sensors/` `[MAJOR]`

### 6. Operators (if `operators/` files changed)
- [ ] `execute(self, context: Context)` is defined `[BLOCKER]`
- [ ] `super().__init__(**kwargs)` is called in `__init__` `[BLOCKER]`
- [ ] All params are keyword-only (`*` before params) `[MAJOR]`
- [ ] `template_fields` declared for all Jinja-templatable params `[MAJOR]`
- [ ] No business logic in `execute()` — delegates to `service/` `[MAJOR]`
- [ ] `AirflowException` raised on failure (not raw exceptions) `[MAJOR]`
- [ ] `self.log` used for logging — not `print()` or `logging` `[MAJOR]`

### 7. Sensors (if `sensors/` files changed)
- [ ] `poke(self, context: Context) -> bool` is defined `[BLOCKER]`
- [ ] `mode="reschedule"` is the default — not `poke` `[MAJOR]`
- [ ] `timeout` is bounded — set via `kwargs.setdefault` `[MAJOR]`
- [ ] Transient errors return `False` — permanent errors raise `AirflowException` `[MAJOR]`
- [ ] GCS `list_blobs` always uses a `prefix` filter — never lists entire bucket `[MAJOR]`

### 8. Service Layer (if `service/` files changed)
- [ ] No GCP client instantiated at module level `[BLOCKER]`
- [ ] All GCP calls have explicit `timeout` parameter `[MAJOR]`
- [ ] `GoogleAPICallError` caught and re-raised as `PluginServiceError` `[MAJOR]`
- [ ] No Airflow imports `[BLOCKER]`
- [ ] REST API calls use `response.raise_for_status()` `[MAJOR]`
- [ ] No PII or secret values logged `[BLOCKER]`

### 9. Utility Layer (if `utility/` files changed)
- [ ] No Airflow imports `[BLOCKER]`
- [ ] Secret values never logged — `data_mask.py` used before logging `[BLOCKER]`
- [ ] All secret access goes through `utility/secrets/` — not direct GSM calls `[BLOCKER]`
- [ ] `gcs_client_singleton.py` changes include a `reset_*` function for tests `[MAJOR]`
- [ ] Config validator YAML changes are backward compatible `[MAJOR]`

### 10. Python Quality
- [ ] All public functions/classes have Google-style docstrings `[MAJOR]`
- [ ] All function signatures have type hints `[MAJOR]`
- [ ] No `print()` anywhere in source layers `[MAJOR]`
- [ ] No mutable default arguments `[BLOCKER]`
- [ ] No bare `except:` or `except Exception: pass` `[BLOCKER]`
- [ ] Logging uses `%s` lazy formatting — not f-strings `[NIT]`

### 11. Tests
- [ ] Every new or modified operator/sensor/service has a test `[MAJOR]`
- [ ] Tests cover happy path AND at least one failure/edge case `[MAJOR]`
- [ ] All GCS/BQ/Dataproc/GSM calls are mocked — no real GCP in unit tests `[BLOCKER]`
- [ ] `gsm_e2e.py` is not modified unless intentional and reviewed separately `[MAJOR]`
- [ ] Test names follow `test_<unit>_<scenario>_<expected_outcome>` `[MINOR]`
- [ ] Coverage does not decrease from base branch `[MAJOR]`

---

## 📋 Review Comment Format

```
[SEVERITY] Short title

Problem: What is wrong and why it matters for production DAGs
Location: `filename.py`, line N
Suggestion:

    # corrected code here

Reference: .github/instructions/<layer>.instructions.md
```

---

## 🏁 Review Decision Rules

| Condition | Decision |
|---|---|
| Any `[BLOCKER]` present | ❌ Request Changes — do not approve |
| Any unresolved `[MAJOR]` | ❌ Request Changes — do not approve |
| Only `[MINOR]` / `[NIT]` issues | ⚠️ Comment only — do not block |
| All checklist items pass | ✅ Approve — ready for human reviewer |
