# Pre-Review Gate — Complete Documentation

### `scripts/pre_review_gate.py` | `airflow_plugins` Wheel Source Repo

---

## 📖 Table of Contents

1. [The Story — How This Idea Was Born](#1-the-story--how-this-idea-was-born)
2. [What Is the Pre-Review Gate?](#2-what-is-the-pre-review-gate)
3. [Why Do We Need It Before Copilot Review?](#3-why-do-we-need-it-before-copilot-review)
4. [What Does It Do?](#4-what-does-it-do)
5. [All 13 Gates — Detailed Explanation](#5-all-13-gates--detailed-explanation)
6. [SonarQube & Fortify Coverage — How We Get ~80%](#6-sonarqube--fortify-coverage--how-we-get-80)
7. [How This Helps Our Team in the Modern Era](#7-how-this-helps-our-team-in-the-modern-era)
8. [How to Install — Complete Setup Guide](#8-how-to-install--complete-setup-guide)
9. [How to Run](#9-how-to-run)
10. [Disabling Individual Gates](#10-disabling-individual-gates)
11. [Expected Output — Gate by Gate](#11-expected-output--gate-by-gate)
12. [Frequently Asked Questions](#12-frequently-asked-questions)

---

## 1. The Story — How This Idea Was Born

> *"The best tools come from experiencing the pain they solve."*

### The Problem Aparup Faced

Working on the `airflow_plugins` wheel source repo, Aparup noticed a recurring pattern that was slowing the entire team down.

A developer would spend hours writing a new operator or service script, open a pull request, and then wait. The PR would sit in the queue while:

- **SonarQube** ran its full pipeline scan — taking 20–40 minutes
- **Fortify** ran its deep SAST analysis — sometimes taking over an hour
- **Copilot Code Review** left dozens of comments about formatting, missing type hints, and `print()` statements that had nothing to do with the actual logic

By the time real feedback arrived, the developer had already context-switched to something else. Fixing mechanical issues — a missing type hint, a `print()` left in `service/bigquery.py`, an import in the wrong order — meant going back, re-reading the code, making tiny fixes, and waiting for the entire pipeline to run again.

The cycle looked like this:

```
Write code → Open PR → Wait 40 mins → Get 15 comments
→ Fix 13 mechanical issues → Push → Wait 40 mins again
→ Get 2 real logic comments → Fix → Push → Wait again...
```

**Total time wasted on mechanical issues: hours per PR.**

### The Brainstorm

Aparup asked a simple question:

> *"What if every developer could run the same checks that SonarQube, Fortify, and Copilot perform — in 60 seconds, on their own laptop, before they even push?"*

The insight was that most of what these enterprise tools catch falls into two categories:

1. **Mechanical issues** — formatting, linting, type hints, imports — things a local script catches instantly
2. **Security and vulnerability issues** — patterns that open-source tools like `semgrep`, `pip-audit`, and `detect-secrets` already check for, for free

The result was `pre_review_gate.py` — a single Python script that runs 13 sequential checks, gives immediate feedback with exact file and line numbers, and either confirms the code is ready for review or tells the developer exactly what to fix.

**The goal:** By the time a PR is opened, every mechanical and security issue is already resolved. Copilot and human reviewers focus only on architecture, logic, and business correctness — the things that actually require human judgement.

---

## 2. What Is the Pre-Review Gate?

The Pre-Review Gate is a **Python script** that runs locally on a developer's machine before they open a pull request. It is the quality checkpoint between writing code and requesting review.

```
Developer finishes coding
          ↓
python scripts/pre_review_gate.py
          ↓
  ┌──────────────────────────────────────┐
  │  13 automated checks in ~60 seconds  │
  └──────────────────────────────────────┘
          ↓
  All pass?                  Any fail?
     ↓                           ↓
  Open PR               Fix issues → re-run
     ↓
  Copilot Code Review activates
  (reads .github/instructions/ rules)
     ↓
  Human reviewer assigned
```

### Key Facts

| Property | Value |
|---|---|
| Language | Pure Python — no bash, no shell knowledge needed |
| Run time | ~30–60 seconds (without tests), ~2–3 minutes (with tests) |
| Location | `scripts/pre_review_gate.py` in repo root |
| Requires | Python 3.10+ |
| Network | Offline except Gate 12 (`pip-audit` CVE database lookup) |

---

## 3. Why Do We Need It Before Copilot Review?

### The Problem with Going Straight to Copilot

GitHub Copilot Code Review is powerful — it understands architecture, patterns, and the rules in our `.github/instructions/` files. But it reviews whatever code you give it, including code full of formatting errors, missing type hints, and debug `print()` statements.

```
❌ Without Pre-Review Gate — Copilot review looks like this:

  [MINOR] Line 47: Missing type hint on execute()
  [MINOR] Line 52: Use self.log instead of print()
  [MINOR] Line 61: Import order incorrect
  [MINOR] Line 88: Line too long (103 chars)
  [MAJOR] Line 112: print() in service layer
  [NIT]   Line 130: f-string in logging call
  ... 15 more mechanical comments ...
  [MAJOR] Line 203: No test for this new method   ← the real issue, buried
```

```
✅ With Pre-Review Gate — Copilot review looks like this:

  [MAJOR] Line 203: No test for this new method
  [MAJOR] Line 215: Operator contains GCP logic — move to service/
  [MINOR] Line 220: Consider retry logic for transient GCS errors
```

**Three focused, high-value comments. This is what Copilot review is for.**

### The Broader Why

| Without Pre-Review Gate | With Pre-Review Gate |
|---|---|
| Copilot reviews messy code | Copilot reviews clean code |
| 20+ mechanical comments per PR | 2–5 architectural comments per PR |
| Developer fixes formatting under review pressure | Developer fixes formatting privately in 10 seconds |
| SonarQube finds issues after 40-minute wait | Issues found in 60 seconds locally |
| Fortify flags secrets after pipeline run | Secrets caught before first push |
| Human reviewer wastes time on style | Human reviewer focuses on logic |

---

## 4. What Does It Do?

The script runs **13 sequential gates**. Each gate is a focused check. If a gate fails, it tells the developer exactly which file, which line, and what to do.

```
Gates 1–4  : Code quality   (formatting, linting, types, security)
Gates 5–9  : Repo rules     (no DAGs, no print(), no bad imports, no secrets)
Gate 10    : Tests           (unit tests + coverage ≥80%)
Gates 11–13: SAST            (SonarQube + Fortify equivalent checks)
Gate 14    : Pylint          (code quality score ≥9.0/10)
```

Individual gates can be **disabled on demand** — see [Section 10](#10-disabling-individual-gates).

---

## 5. All 13 Gates — Detailed Explanation

---

### 🟦 Gate 1 — Black (Code Formatting)

**Tool:** `black`

Black is an opinionated formatter. It enforces line length of 88 characters, consistent quote style, correct spacing, and proper indentation. When every developer uses Black, all code looks identical regardless of who wrote it.

```python
# ❌ Developer wrote this
def execute(self,context:Context)->Any:
    self.log.info("Running for project=%s",self.project_id)

# ✅ Black formats it to this
def execute(self, context: Context) -> Any:
    self.log.info("Running for project=%s", self.project_id)
```

**Auto-fixable:** Yes — `--fix` flag runs Black automatically

---

### 🟦 Gate 2 — Ruff (Linting + Import Order)

**Tool:** `ruff`

| Rule | What it catches |
|---|---|
| `F401` | Unused imports |
| `F403` | `import *` wildcard imports (forbidden) |
| `B006` | Mutable default arguments e.g. `def __init__(self, items=[])` |
| `E722` | Bare `except:` with no exception type |
| `I`    | Import order — stdlib → third-party → local |

Mutable default arguments in operator `__init__` are a `[BLOCKER]` in our Copilot instructions — they cause shared state bugs across DAG runs.

**Auto-fixable:** Most issues — `--fix` flag runs `ruff --fix`

---

### 🟦 Gate 3 — Mypy (Type Checking)

**Tool:** `mypy`

Enforces type hints on all function signatures. Specifically critical for:
- `execute(self, context: Context) -> Any` on every operator
- `poke(self, context: Context) -> bool` on every sensor
- All `service/` and `utility/` public methods

A sensor `poke()` without `-> bool` can silently return `None`, which Airflow treats as `False` — the sensor polls forever.

```python
# ❌ Mypy fails
def copy_file(self, source, destination):
    ...

# ✅ Mypy passes
def copy_file(self, source: str, destination: str) -> bool:
    ...
```

**Auto-fixable:** No — developer must add hints manually

---

### 🟦 Gate 4 — Bandit (Security Scan)

**Tool:** `bandit`

Python-specific security vulnerabilities:
- Use of `eval()` or `exec()` on any input
- Hardcoded password patterns
- Insecure `subprocess` calls
- Weak cryptography algorithms

`service/` scripts handle GCS, BigQuery, Dataproc, and GSM. A security issue here reaches every production DAG across the organisation.

---

### 🟥 Gate 5 — No DAG Constructs (BLOCKER)

**Tool:** Python `ast` + string search

Scans every `.py` file for:
- `with DAG(`
- `from airflow.models import DAG`
- `from airflow import DAG`

This is a wheel source repo. DAG definitions have no business being here. **This is a `[BLOCKER]` — the PR cannot proceed if this fails.**

---

### 🟥 Gate 6 — No `print()` (MAJOR)

**Tool:** Python `ast.parse()` — reads actual code structure, not text patterns

| Layer | Required logging method |
|---|---|
| `operators/` | `self.log.info()` / `self.log.error()` |
| `sensors/` | `self.log.info()` / `self.log.warning()` |
| `service/` | `logging.getLogger(__name__)` |
| `utility/` | `logging.getLogger(__name__)` |
| `generator/` | `logging.getLogger(__name__)` |

In production Airflow, `print()` output is not captured by the task logger — it goes nowhere. Without `self.log`, debugging failed tasks in production is nearly impossible.

Uses `ast.parse()` so it never false-positives on comments or strings that contain the word "print".

---

### 🟥 Gate 7 — No Module-Level GCP Clients (BLOCKER)

**Tool:** Python `ast.iter_child_nodes()`

Finds GCP client instantiations (`bigquery.Client`, `storage.Client`, `secretmanager.`, `dataproc_v1.`) at the **top level of a file** — outside any function or class.

Airflow's scheduler constantly re-parses all wheel modules on every heartbeat. A module-level GCP client:
1. **Fails immediately** in environments without credentials (local dev, CI)
2. **Slows the Composer scheduler** on every parse cycle
3. **Exhausts GCP API quota** just from module imports

```python
# ❌ Module level — BLOCKER
client = storage.Client(project="my-project")  # runs at every import

# ✅ Lazy init — runs only when task executes
@property
def client(self) -> storage.Client:
    if self._client is None:
        self._client = storage.Client(project=self._project_id)
    return self._client
```

---

### 🟥 Gate 8 — No Airflow Imports in Lower Layers (BLOCKER)

**Tool:** Python `ast` — inspects `Import` and `ImportFrom` nodes

Checks `service/`, `utility/`, and `generator/` for `from airflow...` or `import airflow`.

These layers must be pure Python — independently testable without Airflow installed. If `service/bigquery.py` imports Airflow, you cannot unit test it without a full Airflow environment.

```python
# ❌ Forbidden in service/ utility/ generator/
from airflow.exceptions import AirflowException

# ✅ Use domain exception instead
from airflow_plugins.utility.exceptions import PluginServiceError
```

---

### 🟥 Gate 9 — No Hardcoded Secrets (BLOCKER)

**Tool:** `re.compile()` with targeted patterns

Scans for: `password = "..."`, `api_key = "..."`, `token = "..."`, `secret = "..."`, AWS key format (`AKIA...`).

All secrets must go through `utility/secrets/` GSM client abstraction. Gate 13 (`detect-secrets`) provides even deeper secret detection.

---

### 🟩 Gate 10 — Pytest + Coverage

**Tool:** `pytest` with `pytest-cov`

- All tests in `airflow_plugins/unit_test/` must pass
- Coverage across `airflow_plugins/` must be **at least 80%**
- `gsm_e2e.py` is **explicitly excluded** — requires real GCP, not a unit test

The 80% floor ensures all critical paths in operators, sensors, and services are covered before any version ships.

---

### 🟪 Gate 11 — Semgrep OWASP + Python Security *(Fortify equivalent)*

**Tool:** `semgrep`

| Ruleset | What it scans for |
|---|---|
| `p/python` | Python-specific bug patterns |
| `p/owasp-top-ten` | All OWASP Top 10 vulnerability categories |
| `p/secrets` | Secret and credential patterns |
| `p/security-audit` | General security audit |

**OWASP coverage:**

| OWASP Category | Semgrep detects |
|---|---|
| A01 Broken Access Control | Path traversal, directory escape |
| A02 Cryptographic Failures | Weak hash algorithms (MD5, SHA1) |
| A03 Injection | SQL, command, LDAP injection |
| A05 Security Misconfiguration | Debug mode enabled |
| A07 Auth Failures | Hardcoded credentials |
| A08 Software Integrity | Insecure deserialization |

Maps to Fortify's Python SAST analyser — same categories, same patterns.

---

### 🟪 Gate 12 — pip-audit CVE Scan *(SonarQube dependency scan equivalent)*

**Tool:** `pip-audit`

Checks every package in your environment against:
- **OSV database** — Google-maintained Open Source Vulnerability database
- **PyPI advisory database** — Security advisories published on PyPI

Behaviour:
- **Fails** only if there are vulnerabilities with a known fix available
- **Warns but passes** for vulnerabilities with no fix yet (unfixable)

Maps to SonarQube's dependency vulnerability scanning feature.

---

### 🟪 Gate 13 — detect-secrets Deep Credential Scan *(Fortify credential scan equivalent)*

**Tool:** `detect-secrets`

Far more thorough than Gate 9 regex patterns. Detects:

| Secret Type | Example Pattern |
|---|---|
| AWS Access Keys | `AKIA...` |
| GCP Service Account Keys | JSON key file content |
| Private Keys | RSA, EC private key blocks |
| GitHub Tokens | `ghp_...` |
| Slack Tokens | `xoxb-...` |
| Basic Auth in URLs | `https://user:password@host` |
| Base64 Encoded Credentials | Encoded secrets in code |
| High-Entropy Strings | Random-looking strings likely to be secrets |

Maps to Fortify's credential and secret detection module.

---

### 🟨 Gate 14 — Pylint Score ≥ 9.0/10 *(SonarQube code quality score equivalent)*

**Tool:** `pylint`
**Minimum score:** 9.0 / 10.0

Runs a full pylint analysis across all `airflow_plugins/` source layers. Pylint scores your code out of 10 based on the number and severity of issues found. A score of 9.0 or above means your code has very few quality issues.

**What pylint checks that other gates don't:**

| Pylint Check | Code | What it catches |
|---|---|---|
| Duplicate code | `R0801` | Copy-pasted blocks across files — the SonarQube gap we mentioned |
| Cyclomatic complexity | `R0912` | Functions with too many branches (hard to test and maintain) |
| Too many arguments | `R0913` | Functions with too many parameters (design smell) |
| Too many branches | `R0912` | Nested logic beyond acceptable depth |
| Too many statements | `R0915` | Functions doing too much — should be split |
| Too many return statements | `R0911` | Complex exit logic |
| Too many instance attributes | `R0902` | Classes holding too much state |
| Unused variables | `W0612` | Variables assigned but never used |
| Unreachable code | `W0101` | Code after a `return` statement |

**Rules intentionally disabled** (already covered by other gates):
- `C0301` line-too-long → Black handles this (Gate 1)
- `W0611` unused-import → Ruff handles this (Gate 2)
- `E0401` import-error → Mypy handles this (Gate 3)

**Score output — colour coded:**
```
# Score passes
  Score: 9.42/10  (minimum: 9.0/10) ✔

# Score fails
  Score: 7.83/10  (minimum: 9.0/10) ✘
  Score is below the required 9.0/10 threshold

# Individual issues colour coded:
  [E] errors    → red
  [W] warnings  → yellow
  [R] refactor  → cyan
  [C] convention → grey
```

**Why 9.0 is the right threshold for this repo:**
A score below 9.0 in a wheel package means there are enough quality issues to affect maintainability across all teams consuming the wheel. 9.0 allows for minor imperfections while ensuring the codebase stays clean and consistent.

---

## 6. SonarQube & Fortify Coverage — How We Get ~80%

### Coverage Mapping

```
┌────────────────────────────────────────────────────────────────┐
│                     FORTIFY Coverage                           │
├──────────────────────────────┬─────────────────────────────────┤
│ Fortify Feature              │ Our Gate                        │
├──────────────────────────────┼─────────────────────────────────┤
│ SAST — Security patterns     │ Gate 11 — semgrep (OWASP)       │
│ Credential scan              │ Gate 13 — detect-secrets        │
│ Python vuln patterns         │ Gate  4 — bandit                │
│ Dependency CVEs              │ Gate 12 — pip-audit             │
├──────────────────────────────┴─────────────────────────────────┤
│                    SONARQUBE Coverage                          │
├──────────────────────────────┬─────────────────────────────────┤
│ SonarQube Feature            │ Our Gate                        │
├──────────────────────────────┼─────────────────────────────────┤
│ Code smells                  │ Gate  2 — ruff                  │
│ Formatting                   │ Gate  1 — black                 │
│ Type safety                  │ Gate  3 — mypy                  │
│ Test coverage                │ Gate 10 — pytest --cov          │
│ Security hotspots            │ Gate  4 — bandit                │
│ Dependency scan              │ Gate 12 — pip-audit             │
│ Duplicate code               │ Gate 14 — pylint (R0801)        │
│ Code quality score           │ Gate 14 — pylint score ≥9.0     │
└──────────────────────────────┴─────────────────────────────────┘
```

### What We Don't Cover (~5%)

| Gap | Reason |
|---|---|
| Historical trend tracking | SonarQube tracks debt over time — local tools don't |
| Quality gate enforcement in pipeline | Only real Sonar/Fortify can block merge in CI |
| Fortify deep taint analysis | Tracks data flow across 10+ files — semgrep is shallower |

### The Value Proposition

> **Before:** Wait 40 minutes for Sonar/Fortify to find 15 issues.
> **After:** Find 12 of those 15 issues in 60 seconds, before pushing.

The real SonarQube and Fortify pipeline runs become **confirmation**, not **discovery**.

---

## 7. How This Helps Our Team in the Modern Era

### For Individual Developers

| Old way | New way |
|---|---|
| Push → wait for CI → get feedback | Check locally → push clean code |
| Context-switch while waiting | Fix immediately while code is fresh |
| Discover security issues in CI | Catch them in 60 seconds |
| Learn from reviewer comments | Learn from gate output instantly |

### For Code Reviewers

- PRs arrive already formatted, linted, typed, and tested
- No time wasted on mechanical comments
- Review energy focused on architecture and business logic
- Faster review cycles — less back-and-forth

### For Copilot Code Review

- Reads clean, well-structured code
- `.github/instructions/` rules activate on real issues
- `[BLOCKER]` and `[MAJOR]` comments are meaningful, not mechanical

### For the Organisation

- Wheel quality improves — every version has passed 13 checks
- Production DAG stability improves — fewer broken operators reach GCS
- Onboarding improves — new developers get instant, specific feedback
- SonarQube/Fortify pipeline finds fewer issues — faster CI cycles

### In the AI-Assisted Development Era

With GitHub Copilot helping developers write code faster, the risk of mechanical issues creeping in actually **increases** — AI-generated code may not follow your team's specific layer boundaries or security patterns.

The gate acts as a **convention enforcer** alongside AI tooling:

```
Copilot Chat helps write the code faster
          ↓
pre_review_gate.py ensures it follows our conventions
          ↓
Copilot Code Review focuses on architecture
          ↓
Human reviewer makes the final call
```

---

## 8. How to Install — Complete Setup Guide

### Prerequisites

- Python **3.10 or higher**
- `pip` (comes with Python)
- Access to the `airflow_plugins` repo

Check your Python version:
```bash
python --version
# Should show Python 3.10.x or higher
```

---

### Step 1 — Install Core Tools (Required)

These 5 tools are required. Gates 1–10 will not run without them.

```bash
pip install \
  black==24.3.0 \
  ruff==0.4.1 \
  mypy==1.9.0 \
  bandit==1.7.8 \
  pytest==8.1.1 \
  pytest-cov==5.0.0 \
  pytest-mock==3.14.0
```

Or install the latest versions (no pinning):
```bash
pip install black ruff mypy bandit pytest pytest-cov pytest-mock
```

---

### Step 2 — Install SAST Tools (Strongly Recommended)

These 3 tools power Gates 11–13. If not installed, those gates warn but do not block. However, they are strongly recommended — they provide your SonarQube and Fortify equivalent coverage.

```bash
pip install \
  semgrep \
  pip-audit \
  detect-secrets
```

---

### Step 3 — Install All at Once (Recommended)

The simplest approach — install everything in one command:

```bash
pip install \
  black \
  ruff \
  mypy \
  bandit \
  pytest \
  pytest-cov \
  pytest-mock \
  semgrep \
  pip-audit \
  detect-secrets \
  pylint
```

---

### Step 4 — Verify Installation

Run this to confirm all tools are found and print their versions:

```bash
python scripts/pre_review_gate.py --skip-tests --skip-sast
```

You should see the tool version list in the header:

```
  Core tools:
  ℹ  black            black, 24.3.0
  ℹ  ruff             ruff 0.4.1
  ℹ  mypy             mypy 1.9.0
  ℹ  bandit           bandit 1.7.8
  ℹ  pytest           pytest 8.1.1

  SAST tools (Gates 11-13):
  ℹ  semgrep          installed
  ℹ  pip-audit        installed
  ℹ  detect-secrets   installed
```

---

### Tool Version Reference

| Tool | Purpose | Gate | Install command |
|---|---|---|---|
| `black` | Code formatting | 1 | `pip install black` |
| `ruff` | Linting + import order | 2 | `pip install ruff` |
| `mypy` | Type checking | 3 | `pip install mypy` |
| `bandit` | Security scan | 4 | `pip install bandit` |
| `pytest` | Unit test runner | 10 | `pip install pytest` |
| `pytest-cov` | Coverage reporting | 10 | `pip install pytest-cov` |
| `pytest-mock` | Mocking in tests | 10 | `pip install pytest-mock` |
| `semgrep` | OWASP + SAST | 11 | `pip install semgrep` |
| `pip-audit` | CVE dependency scan | 12 | `pip install pip-audit` |
| `detect-secrets` | Deep credential scan | 13 | `pip install detect-secrets` |
| `pylint` | Code quality score | 14 | `pip install pylint` |

---

### Optional: Save to `requirements-dev.txt`

Add a `requirements-dev.txt` file at the repo root so every new developer can install everything with one command:

```
# requirements-dev.txt
# Development tools — pre-review gate and testing
black
ruff
mypy
bandit
pytest
pytest-cov
pytest-mock
semgrep
pip-audit
detect-secrets
pylint
```

```bash
# New developer setup — one command
pip install -r requirements-dev.txt
```

---

## 9. How to Run

### List all available gates first

```bash
python scripts/pre_review_gate.py --list-gates
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Available Gates — airflow_plugins Pre-Review Gate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #     Name                                Category
  ───── ─────────────────────────────────── ───────────────
  1     Black                               Code Quality
  2     Ruff                                Code Quality
  3     Mypy                                Code Quality
  4     Bandit                              Code Quality
  5     No DAG Constructs                   Repo Rules
  6     No print()                          Repo Rules
  7     No Module-Level GCP                 Repo Rules
  8     No Airflow in Lower Layers          Repo Rules
  9     No Hardcoded Secrets                Repo Rules
  10    Pytest                              Tests
  11    Semgrep                             SAST
  12    pip-audit                           SAST
  13    detect-secrets                      SAST
  14    Pylint Score                        Code Quality
```

---

### Standard run — all 13 gates

```bash
python scripts/pre_review_gate.py
```

### Auto-fix formatting, then run all gates

```bash
python scripts/pre_review_gate.py --fix
```

Runs `black` and `ruff --fix` automatically before checking. Use when you want formatting corrected for you rather than just reported.

### Skip pytest — quick lint check

```bash
python scripts/pre_review_gate.py --skip-tests
```

Shortcut for `--disable 10`. Useful during active development when you want fast lint/type feedback without the full test suite.

### Skip SAST gates — fastest check

```bash
python scripts/pre_review_gate.py --skip-sast
```

Shortcut for `--disable 11 --disable 12 --disable 13`. Useful for quick code quality checks.

### Combined flags

```bash
# Fix formatting + skip tests + skip SAST (fastest possible run)
python scripts/pre_review_gate.py --fix --skip-tests --skip-sast
```

### Recommended developer workflow

```bash
# While actively writing code — fast feedback, no tests
python scripts/pre_review_gate.py --skip-tests --skip-sast

# Before committing — full quality + test check
python scripts/pre_review_gate.py

# Before opening PR — everything including SAST
python scripts/pre_review_gate.py
```

---

## 10. Disabling Individual Gates

Sometimes a specific gate needs to be temporarily bypassed — for example, a dependency CVE with no fix available yet, or a SAST rule that conflicts with a known project-level exception. The `--disable` flag handles this cleanly.

### How to disable

**By gate number:**
```bash
python scripts/pre_review_gate.py --disable 12
```

**By gate name (case-insensitive, partial match accepted):**
```bash
python scripts/pre_review_gate.py --disable "Bandit"
python scripts/pre_review_gate.py --disable "bandit"   # same
python scripts/pre_review_gate.py --disable "pip"      # matches pip-audit
```

**Multiple gates at once:**
```bash
python scripts/pre_review_gate.py --disable 11 --disable 12 --disable 13
```

**Combined with other flags:**
```bash
python scripts/pre_review_gate.py --fix --disable 12
python scripts/pre_review_gate.py --skip-tests --disable 11
```

---

### What a disabled gate looks like in output

When a gate is disabled it is shown clearly — it does not silently vanish:

```
[Gate 12] pip-audit — Dependency CVE Scan (SonarQube equivalent)
  ⊘ DISABLED  pip-audit — Dependency CVE Scan
               (manually disabled via --disable flag)
```

At the top of the run, all disabled gates are listed upfront:

```
  ⚠  Disabled gates:
     Gate 12: pip-audit
     These gates will NOT run. Ensure you have a valid reason.
```

And in the final summary — a reminder is always shown so nobody forgets:

```
  ⊘  1 gate(s) were disabled and did not run:
     • Gate 12: pip-audit — Dependency CVE Scan

  ✔ All 12 active gate(s) passed — safe to open PR
  ⚠  Remember: 1 gate(s) were skipped — re-enable before final merge
```

---

### When is it acceptable to disable a gate?

| Situation | Acceptable? | Recommended action |
|---|---|---|
| Dependency CVE with no fix yet | ✅ Yes | Disable Gate 12, add comment in PR |
| Waiting on a library upgrade | ✅ Yes | Disable temporarily, track in ticket |
| SAST false positive you've reviewed | ✅ Yes | Disable Gate 11, add inline comment |
| "Tests are slow right now" | ⚠️ Avoid | Use `--skip-tests` for local dev only — never for final PR |
| "I'll fix the type hints later" | ❌ No | Fix them before PR — that's the point |
| Disabling `[BLOCKER]` gates (5, 7, 8, 9) | ❌ Never | These protect production DAGs |

---

## 11. Expected Output — Gate by Gate

### Header (always shown)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔍 Pre-Review Gate — airflow_plugins Wheel Source Repo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Core tools:
  ℹ  black            black, 24.3.0
  ℹ  ruff             ruff 0.4.1
  ℹ  mypy             mypy 1.9.0
  ℹ  bandit           bandit 1.7.8
  ℹ  pytest           pytest 8.1.1

  SAST tools (Gates 11-13):
  ℹ  semgrep          installed
  ℹ  pip-audit        installed
  ℹ  detect-secrets   installed
```

---

### Gate 1 — Black

**Pass:**
```
[Gate 1] Black — Code Formatting
  ✔ PASS  Black — Code Formatting
```

**Fail:**
```
[Gate 1] Black — Code Formatting
  --- airflow_plugins/operators/dataproc.py
  +++ airflow_plugins/operators/dataproc.py (reformatted)
  @@ -45 @@
  -    def execute(self,context:Context)->Any:
  +    def execute(self, context: Context) -> Any:
  ✘ FAIL  Black — Code Formatting
```

---

### Gate 2 — Ruff

**Pass:**
```
[Gate 2] Ruff — Linting + Import Order
  ✔ PASS  Ruff — Linting + Import Order
```

**Fail:**
```
[Gate 2] Ruff — Linting + Import Order
  airflow_plugins/operators/dataproc.py:12:1: F401 `os` imported but unused
  airflow_plugins/service/bigquery.py:34:32: E722 Do not use bare `except`
  airflow_plugins/operators/variable.py:28:5: B006 Do not use mutable data
      structures for argument defaults
  ✘ FAIL  Ruff — Linting + Import Order
```

---

### Gate 3 — Mypy

**Pass:**
```
[Gate 3] Mypy — Type Checking
  Success: no issues found in 24 source files
  ✔ PASS  Mypy — Type Checking
```

**Fail:**
```
[Gate 3] Mypy — Type Checking
  airflow_plugins/service/gcs_file_merge.py:67: error: Function is missing
      a return type annotation  [no-untyped-def]
  airflow_plugins/operators/dataproc.py:45: error: Incompatible return value
      type  [return-value]
  Found 2 errors in 2 files
  ✘ FAIL  Mypy — Type Checking
```

---

### Gate 4 — Bandit

**Pass:**
```
[Gate 4] Bandit — Security Scan
  ✔ PASS  Bandit — Security Scan
```

**Fail:**
```
[Gate 4] Bandit — Security Scan
  >> Issue: [B105:hardcoded_password_string] Possible hardcoded password
     Severity: Medium   Confidence: Medium
     Location: airflow_plugins/service/flow.py:89
  ✘ FAIL  Bandit — Security Scan
```

---

### Gate 5 — No DAG Constructs

**Pass:**
```
[Gate 5] No DAG Constructs in Wheel Source [BLOCKER]
  No DAG constructs found — clean
  ✔ PASS  No DAG Constructs in Wheel Source [BLOCKER]
```

**Fail:**
```
[Gate 5] No DAG Constructs in Wheel Source [BLOCKER]
  [BLOCKER] 'with DAG(' found in airflow_plugins/operators/dataproc.py
            DAG constructs do not belong in this wheel source repo
  ✘ FAIL  No DAG Constructs in Wheel Source [BLOCKER]
```

---

### Gate 6 — No `print()`

**Pass:**
```
[Gate 6] No print() in Any Layer [MAJOR]
  No print() statements found — clean
  ✔ PASS  No print() in Any Layer [MAJOR]
```

**Fail:**
```
[Gate 6] No print() in Any Layer [MAJOR]
  [MAJOR] print() in airflow_plugins/service/bigquery.py:47
          Use logging.getLogger(__name__) in service/
  [MAJOR] print() in airflow_plugins/operators/dataproc.py:112
          Use self.log in operators/
  ✘ FAIL  No print() in Any Layer [MAJOR]
```

---

### Gate 7 — No Module-Level GCP Clients

**Pass:**
```
[Gate 7] No Module-Level GCP Client Instantiation [BLOCKER]
  No module-level GCP clients found — clean
  ✔ PASS  No Module-Level GCP Client Instantiation [BLOCKER]
```

**Fail:**
```
[Gate 7] No Module-Level GCP Client Instantiation [BLOCKER]
  [BLOCKER] Module-level GCP client in airflow_plugins/service/bigquery.py:8
            Move 'bigquery.Client(' inside a method or @property
  ✘ FAIL  No Module-Level GCP Client Instantiation [BLOCKER]
```

---

### Gate 8 — No Airflow Imports in Lower Layers

**Pass:**
```
[Gate 8] No Airflow Imports in service/ utility/ generator/ [BLOCKER]
  No forbidden Airflow imports in service/utility/generator — clean
  ✔ PASS  No Airflow Imports in service/ utility/ generator/ [BLOCKER]
```

**Fail:**
```
[Gate 8] No Airflow Imports in service/ utility/ generator/ [BLOCKER]
  [BLOCKER] Airflow import in airflow_plugins/service/dataproc.py:5
            service/ must not depend on Airflow
  ✘ FAIL  No Airflow Imports in service/ utility/ generator/ [BLOCKER]
```

---

### Gate 9 — No Hardcoded Secrets

**Pass:**
```
[Gate 9] No Hardcoded Secrets [BLOCKER]
  No hardcoded secrets found — clean
  ✔ PASS  No Hardcoded Secrets [BLOCKER]
```

**Fail:**
```
[Gate 9] No Hardcoded Secrets [BLOCKER]
  [BLOCKER] Possible hardcoded secret in airflow_plugins/service/flow.py
            Use utility/secrets/ GSM client instead
  ✘ FAIL  No Hardcoded Secrets [BLOCKER]
```

---

### Gate 10 — Pytest + Coverage

**Pass:**
```
[Gate 10] Pytest — Unit Tests + Coverage ≥80% (excludes gsm_e2e.py)
  24 passed in 3.42s

  Name                                         Stmts   Miss  Cover
  ----------------------------------------------------------------
  airflow_plugins/operators/dataproc.py           45      4    91%
  airflow_plugins/service/bigquery.py             78      9    88%
  airflow_plugins/utility/data_mask.py            22      2    91%
  ----------------------------------------------------------------
  TOTAL                                          312     38    88%

  ✔ PASS  Pytest — Unit Tests + Coverage ≥80% (excludes gsm_e2e.py)
```

**Fail:**
```
[Gate 10] Pytest — Unit Tests + Coverage ≥80% (excludes gsm_e2e.py)
  FAILED unit_test/operators/test_dataproc.py::test_execute
      AssertionError: Expected AirflowException, got RuntimeError

  Coverage: 61%  (required: ≥80%)
  ✘ FAIL  Pytest — Unit Tests + Coverage ≥80% (excludes gsm_e2e.py)
```

---

### Gate 11 — Semgrep

**Pass:**
```
[Gate 11] Semgrep — OWASP Top 10 + Python Security (Fortify equivalent)
  Running OWASP Top 10 + Python security ruleset...
  No OWASP / security issues found — clean
  ✔ PASS  Semgrep — OWASP Top 10 + Python Security (Fortify equivalent)
```

**Fail:**
```
[Gate 11] Semgrep — OWASP Top 10 + Python Security (Fortify equivalent)
  [FORTIFY-EQUIV] airflow_plugins/service/file_download_rest_api.py:34
      python.lang.security.audit.subprocess-injection
      User input passed to subprocess — potential command injection
  ✘ FAIL  Semgrep — OWASP Top 10 + Python Security (Fortify equivalent)
```

---

### Gate 12 — pip-audit

**Pass:**
```
[Gate 12] pip-audit — Dependency CVE Scan (SonarQube equivalent)
  Scanning dependencies against OSV + PyPI advisory database...
  No known CVEs found in dependencies — clean
  ✔ PASS  pip-audit — Dependency CVE Scan (SonarQube equivalent)
```

**Fail:**
```
[Gate 12] pip-audit — Dependency CVE Scan (SonarQube equivalent)
  Scanning dependencies against OSV + PyPI advisory database...
  [SONAR-EQUIV] [HIGH] requests==2.27.0 — GHSA-j8r2-6x86-q33q
                Fix available: upgrade to 2.28.0
  [SONAR-EQUIV] [NO FIX YET] some-lib==0.9.1 — CVE-2024-12345
  ✘ FAIL  pip-audit — Dependency CVE Scan (SonarQube equivalent)
```

**Disabled:**
```
[Gate 12] pip-audit — Dependency CVE Scan (SonarQube equivalent)
  ⊘ DISABLED  pip-audit — Dependency CVE Scan
               (manually disabled via --disable flag)
```

---

### Gate 13 — detect-secrets

**Pass:**
```
[Gate 13] detect-secrets — Deep Credential Scan (Fortify equivalent)
  Scanning for credentials, tokens, and API keys...
  No secrets or credentials detected — clean
  ✔ PASS  detect-secrets — Deep Credential Scan (Fortify equivalent)
```

**Fail:**
```
[Gate 13] detect-secrets — Deep Credential Scan (Fortify equivalent)
  Scanning for credentials, tokens, and API keys...
  [FORTIFY-EQUIV] AWS Access Key detected in
      airflow_plugins/service/gcs_to_s3_file_transfer.py:23
      Move to utility/secrets/ GSM client
  ✘ FAIL  detect-secrets — Deep Credential Scan (Fortify equivalent)
```

---

### Gate 14 — Pylint Score

**Pass:**
```
[Gate 14] Pylint — Code Quality Score ≥9.0/10 (SonarQube equivalent)
  Running full pylint analysis (minimum score: 9.0/10)...
  (Maps to: SonarQube code quality score + duplicate code detection)

  Score: 9.42/10  (minimum: 9.0/10) ✔
  ✔ PASS  Pylint — Code Quality Score ≥9.0/10 (SonarQube equivalent)
```

**Fail — score below threshold:**
```
[Gate 14] Pylint — Code Quality Score ≥9.0/10 (SonarQube equivalent)
  Running full pylint analysis (minimum score: 9.0/10)...

  airflow_plugins/service/bigquery.py:45: [R0801(duplicate-code)] Similar
      lines in 2 files — airflow_plugins/service/dataproc.py:38
  airflow_plugins/operators/dataproc.py:88: [R0912(too-many-branches)]
      Too many branches (14/12)
  airflow_plugins/service/flow.py:201: [W0612(unused-variable)]
      Unused variable 'response'

  Score: 7.83/10  (minimum: 9.0/10) ✘
  Score is below the required 9.0/10 threshold
  ✘ FAIL  Pylint — Code Quality Score ≥9.0/10 (SonarQube equivalent)
```

**Disabled:**
```
[Gate 14] Pylint — Code Quality Score ≥9.0/10 (SonarQube equivalent)
  ⊘ DISABLED  Pylint — Code Quality Score ≥9.0/10
               (manually disabled via --disable flag)
```

---

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SonarQube / Fortify coverage summary:
  Fortify SAST                     Gate 11 — semgrep
  SonarQube dependency scan        Gate 12 — pip-audit
  Fortify credential scan          Gate 13 — detect-secrets
  Fortify / Bandit security        Gate  4 — bandit
  SonarQube code quality score     Gate 14 — pylint (≥9.0/10)

  ✔ All 13 gates passed — safe to open PR

  Reminder — manual wheel release steps after merge:
  1. Bump version in pyproject.toml
  2. Update CHANGELOG.md
  3. python -m build
     → dist/airflow_platform_plugins-x.y.z-py3-none-any.whl
  4. gsutil cp dist/*.whl gs://<composer-bucket>/plugins/
  5. Update plugin_version in DAG repo platform_conf.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Final Summary — With Disabled Gates

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⊘  1 gate(s) were disabled and did not run:
     • Gate 12: pip-audit — Dependency CVE Scan

  ✔ All 12 active gate(s) passed — safe to open PR
  ⚠  Remember: 1 gate(s) were skipped — re-enable before final merge
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Final Summary — Failures

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✘ 3 gate(s) failed — do not open PR yet:
    • Gate 5: No DAG Constructs in Wheel Source [BLOCKER]
    • Gate 6: No print() in Any Layer [MAJOR]
    • Gate 10: Pytest — Unit Tests + Coverage ≥80%

  Tip: run python scripts/pre_review_gate.py --fix to
  auto-correct Black and Ruff issues, then re-run.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 12. Frequently Asked Questions

**Q: Does this replace SonarQube and Fortify?**
No — it complements them. It catches ~80% of what they find, locally and instantly. The real pipeline runs become confirmation, not discovery.

**Q: What if a SAST tool isn't installed?**
Gates 11–13 warn but do not fail if `semgrep`, `pip-audit`, or `detect-secrets` are not installed. They are strongly recommended but not hard blockers. Install with `pip install semgrep pip-audit detect-secrets`.

**Q: Can I disable a gate permanently for a project-level exception?**
Yes — add it to a team-agreed config comment in your PR description and track it in a ticket. The `--disable` flag is intentionally not stored in a config file so disabling is always a conscious, visible decision per run.

**Q: Can I add this as a git pre-commit hook?**
Yes. Create `.git/hooks/pre-push`:
```bash
#!/bin/sh
python scripts/pre_review_gate.py --skip-sast
```
Then: `chmod +x .git/hooks/pre-push`

**Q: What is `gsm_e2e.py` and why is it excluded?**
It is an end-to-end test that calls real Google Secret Manager with live credentials. It cannot run offline. It is excluded from the gate and run separately in the integration test pipeline.

**Q: Gate 12 keeps failing because of a CVE with no fix — what do I do?**
Disable it with `--disable 12`, note the CVE in your PR description, and track the dependency upgrade in a ticket. This is exactly the use case `--disable` was built for.

**Q: The gate passes but SonarQube still finds issues — why?**
The ~20% gap is real. SonarQube's historical trend tracking, duplicate code detection, and full technical debt scoring cannot be replicated locally. These are valid findings to fix — the gate reduces the volume so they are easier to address.

**Q: Who maintains this script?**
The script lives in the `airflow_plugins` repo and is versioned alongside the wheel. Any team member can propose changes via PR — the same Copilot review process applies.

---

*Document maintained by the AIRFLOW Platform Engineering team.*
*Script authored by Aparup | Last updated: 2026*
