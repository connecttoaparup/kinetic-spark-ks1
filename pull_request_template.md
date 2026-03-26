## Summary

> What does this PR do? Why is it needed?
> (Replace this line — 2-3 sentences maximum)

---

## Type of Change

<!-- Check all that apply -->

- [ ] 🆕 New operator added (`operators/`)
- [ ] 🆕 New sensor added (`sensors/`)
- [ ] 🆕 New service script added (`service/`)
- [ ] 🆕 New utility added (`utility/`)
- [ ] 🔧 Existing operator/sensor modified
- [ ] 🔧 Existing service/utility modified
- [ ] 🐛 Bug fix
- [ ] ♻️  Refactor (no behaviour change)
- [ ] 📝 Documentation update
- [ ] 🔒 Security fix

---

## Pre-Review Gate

> **Run this before raising the PR:**
> ```bash
> python scripts/pre_review_gate.py
> ```

- [ ] ✔ All 14 gates passed
- [ ] Gate(s) disabled (see reason below): `--disable ___`

**Reason for disabled gate(s):** *(leave blank if none)*

---

## Local Wheel Build

- [ ] Version bumped in `setup.py`
- [ ] `CHANGELOG.md` updated
- [ ] Wheel built locally: `python -m build`
- [ ] Wheel tested locally against a DAG
- [ ] `plugin_version` updated in DAG repo `platform_conf.json`

> After this PR is merged, SRE CI/CD will build the final wheel from `setup.py` version and upload to GCS automatically.

---

## Layer Checklist

### If `operators/` or `sensors/` changed

- [ ] `execute()` / `poke()` defined with correct signature and return type
- [ ] `super().__init__(**kwargs)` called
- [ ] All params are keyword-only (`*` separator used)
- [ ] `template_fields` declared for all Jinja-templatable params
- [ ] No business/GCP logic in `execute()` — delegates to `service/`
- [ ] `AirflowException` raised on failure
- [ ] `self.log` used — no `print()`
- [ ] **No new required params added to existing operators/sensors** ← [BLOCKER]

### If `service/` changed

- [ ] No GCP client at module level — lazy init used
- [ ] All GCP calls have explicit `timeout`
- [ ] `PluginServiceError` raised (not raw GCP exceptions)
- [ ] No `from airflow` imports
- [ ] No `print()` — `logging.getLogger(__name__)` used

### If `utility/` changed

- [ ] No `from airflow` imports
- [ ] Secret values masked with `data_mask.py` before logging
- [ ] Secret access via `utility/secrets/` only
- [ ] `reset_*` function included in singleton changes (for test isolation)

### If `generator/` changed

- [ ] No `from airflow` imports
- [ ] `AIRFLOWConfigError` / `PluginConfigError` raised for missing required keys
- [ ] No operator instantiation — returns typed data only

---

## Backward Compatibility

- [ ] No existing operator/sensor class removed or renamed
- [ ] No existing `__init__` parameter removed or renamed
- [ ] No new **required** parameter added to existing operator/sensor
- [ ] No change to `execute()` return type

**If any box above is unchecked — this is a MAJOR version bump. Document the breaking change:**

```
Breaking change description:
Migration steps for DAG teams:
```

---

## Tests

- [ ] New/modified code has unit tests in `airflow_plugins/unit_test/`
- [ ] Happy path covered
- [ ] At least one failure/edge case covered
- [ ] All GCS / BQ / Dataproc / GSM calls are mocked — no real GCP in tests
- [ ] `gsm_e2e.py` not modified (or modification is intentional — explain below)
- [ ] Coverage did not decrease from base branch

---

## Security

- [ ] No hardcoded secrets, tokens, or credentials
- [ ] All secret access via `utility/secrets/` GSM client
- [ ] No `eval()` or `exec()` on external input
- [ ] No sensitive data logged

---

## Related

<!-- Link any related issues, tickets, or DAG repo PRs -->
- Ticket:
- DAG repo PR:
- Related PR:
