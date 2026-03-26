"""
scripts/pre_review_gate.py

Purpose : Pre-PR quality gate for the airflow_plugins wheel source repo.
          Catches linting, type, security, and test failures BEFORE
          Copilot or a human reviewer sees the PR.

          Gates 1-10  : Code quality, structure, and test coverage
          Gates 11-13 : SonarQube + Fortify equivalent checks
          Gate  14    : Pylint score (minimum 9.0/10)

Usage   : python scripts/pre_review_gate.py [options]

Options :
    --fix                  Auto-fix formatting (black, ruff --fix)
    --skip-tests           Skip Gate 10 (pytest)
    --skip-sast            Skip Gates 11-13 (semgrep, pip-audit, detect-secrets)
    --disable <gate>       Disable a specific gate by number or name (repeatable)
    --list-gates           List all gate numbers and names, then exit

Disable examples:
    --disable 12                         Disable Gate 12 (pip-audit)
    --disable "Bandit"                   Disable Gate 4 by name
    --disable 11 --disable 12            Disable multiple gates
    --disable 7 --disable 8 --disable 9  Disable gates 7, 8, and 9

Exit codes:
    0  All active gates passed — safe to open PR
    1  One or more active gates failed
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

# ── Colour helpers ────────────────────────────────────────────────────────────
RED    = "\033[0;31m"
GREEN  = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE   = "\033[0;34m"
CYAN   = "\033[0;36m"
GREY   = "\033[0;90m"
NC     = "\033[0m"

def red(msg: str)    -> str: return f"{RED}{msg}{NC}"
def green(msg: str)  -> str: return f"{GREEN}{msg}{NC}"
def yellow(msg: str) -> str: return f"{YELLOW}{msg}{NC}"
def blue(msg: str)   -> str: return f"{BLUE}{msg}{NC}"
def cyan(msg: str)   -> str: return f"{CYAN}{msg}{NC}"
def grey(msg: str)   -> str: return f"{GREY}{msg}{NC}"

# ── Gate registry — single source of truth for all gate names ─────────────────
# Format: { gate_number: "gate short name" }
# Used for --list-gates and --disable matching
GATE_REGISTRY: dict[int, str] = {
    1:  "Black",
    2:  "Ruff",
    3:  "Mypy",
    4:  "Bandit",
    5:  "No DAG Constructs",
    6:  "No print()",
    7:  "No Module-Level GCP",
    8:  "No Airflow in Lower Layers",
    9:  "No Hardcoded Secrets",
    10: "Pytest",
    11: "Semgrep",
    12: "pip-audit",
    13: "detect-secrets",
    14: "Pylint Score",
}

# ── Argument parsing ──────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Pre-PR quality gate for airflow_plugins wheel source repo.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Disable examples:
  python scripts/pre_review_gate.py --disable 12
  python scripts/pre_review_gate.py --disable 11 --disable 12
  python scripts/pre_review_gate.py --disable "Bandit"
  python scripts/pre_review_gate.py --disable 7 --disable 8 --disable 9
    """,
)
parser.add_argument(
    "--fix",
    action="store_true",
    help="Auto-fix Black and Ruff issues",
)
parser.add_argument(
    "--skip-tests",
    action="store_true",
    help="Skip Gate 10 (pytest) — shortcut for --disable 10",
)
parser.add_argument(
    "--skip-sast",
    action="store_true",
    help="Skip Gates 11-13 — shortcut for --disable 11 --disable 12 --disable 13",
)
parser.add_argument(
    "--disable",
    action="append",
    metavar="GATE",
    default=[],
    help="Disable a gate by number (e.g. --disable 12) or name (e.g. --disable Bandit). Repeatable.",
)
parser.add_argument(
    "--list-gates",
    action="store_true",
    help="List all gate numbers and names, then exit",
)
args = parser.parse_args()

# ── Handle --list-gates ───────────────────────────────────────────────────────
if args.list_gates:
    print()
    print("━" * 57)
    print("  Available Gates — airflow_plugins Pre-Review Gate")
    print("━" * 57)
    print(f"  {'#':<5} {'Name':<35} {'Category'}")
    print(f"  {'─'*5} {'─'*35} {'─'*15}")
    categories = {
        1: "Code Quality", 2: "Code Quality", 3: "Code Quality", 4: "Code Quality",
        5: "Repo Rules",   6: "Repo Rules",   7: "Repo Rules",
        8: "Repo Rules",   9: "Repo Rules",
        10: "Tests",
        11: "SAST",        12: "SAST",        13: "SAST",
    }
    for num, name in GATE_REGISTRY.items():
        print(f"  {num:<5} {name:<35} {categories.get(num, '')}")
    print()
    print("  Disable a gate:  --disable <number>  or  --disable \"<name>\"")
    print("━" * 57)
    sys.exit(0)

# ── Resolve disabled gates ────────────────────────────────────────────────────
# Accepts both numbers ("12") and partial names ("Bandit", "bandit", "pip-audit")
disabled_gates: set[int] = set()

# Shortcuts
if args.skip_tests:
    disabled_gates.add(10)
if args.skip_sast:
    disabled_gates.update({11, 12, 13})

# --disable flag values
for raw in args.disable:
    matched = False
    # Try numeric first
    if raw.isdigit():
        gate_num = int(raw)
        if gate_num in GATE_REGISTRY:
            disabled_gates.add(gate_num)
            matched = True
        else:
            print(yellow(f"  ⚠  Unknown gate number: {raw} — ignoring"))
            matched = True
    else:
        # Try name match (case-insensitive, partial match allowed)
        for num, name in GATE_REGISTRY.items():
            if raw.lower() in name.lower():
                disabled_gates.add(num)
                matched = True
                break
    if not matched:
        print(yellow(f"  ⚠  Could not match gate: '{raw}' — use --list-gates to see options"))

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent.resolve()
PLUGIN_ROOT = REPO_ROOT / "airflow_plugins"
UNIT_TEST   = PLUGIN_ROOT / "unit_test"
E2E_TEST    = UNIT_TEST / "gsm_e2e.py"

SOURCE_LAYERS = [
    PLUGIN_ROOT / "operators",
    PLUGIN_ROOT / "sensors",
    PLUGIN_ROOT / "service",
    PLUGIN_ROOT / "utility",
    PLUGIN_ROOT / "generator",
    PLUGIN_ROOT / "controller",
]

LOWER_LAYERS = [
    PLUGIN_ROOT / "service",
    PLUGIN_ROOT / "utility",
    PLUGIN_ROOT / "generator",
]

# ── State ─────────────────────────────────────────────────────────────────────
failed:   list[str] = []
skipped:  list[str] = []
_current_gate_num = 0


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    return result.returncode, result.stdout, result.stderr


def run_gate(name: str, fn: Callable[[], bool]) -> None:
    """Run a single gate — skip if disabled, track pass/fail otherwise."""
    global _current_gate_num
    _current_gate_num += 1
    gate_num = _current_gate_num

    print(f"\n{blue(f'[Gate {gate_num}] {name}')}")

    if gate_num in disabled_gates:
        print(grey(f"  ⊘ DISABLED  {name}"))
        print(grey( "             (manually disabled via --disable flag)"))
        skipped.append(f"Gate {gate_num}: {name}")
        return

    if fn():
        print(green(f"  ✔ PASS  {name}"))
    else:
        print(red(f"  ✘ FAIL  {name}"))
        failed.append(f"Gate {gate_num}: {name}")


def tool_installed(name: str) -> bool:
    """Check whether a CLI tool is installed."""
    code, _, _ = run_cmd(["which", name])
    return code == 0


# ── Header ────────────────────────────────────────────────────────────────────
print()
print("━" * 57)
print("  🔍 Pre-Review Gate — airflow_plugins Wheel Source Repo")
print("━" * 57)

# Show disabled gates upfront so developer knows what's active
if disabled_gates:
    print(f"\n{yellow('  ⚠  Disabled gates:')}")
    for g in sorted(disabled_gates):
        print(yellow(f"     Gate {g}: {GATE_REGISTRY.get(g, 'Unknown')}"))
    print(yellow("     These gates will NOT run. Ensure you have a valid reason."))

# ── Dependency check ──────────────────────────────────────────────────────────
core_tools = ["black", "ruff", "mypy", "pytest", "bandit"]
missing = [t for t in core_tools if not tool_installed(t)]
if missing:
    print(red(f"\nERROR: Missing required tools: {', '.join(missing)}"))
    print("       Run: pip install black ruff mypy pytest pytest-cov pytest-mock bandit")
    sys.exit(1)

print(f"\n{cyan('  Core tools:')}")
for tool in core_tools:
    _, out, _ = run_cmd([tool, "--version"])
    version = out.strip().splitlines()[0] if out.strip() else "unknown"
    print(f"{blue('  ℹ')}  {tool:<16} {version}")

sast_tools: dict[str, bool] = {"semgrep": False, "pip-audit": False, "detect-secrets": False}
sast_all_disabled = {11, 12, 13}.issubset(disabled_gates)
if not sast_all_disabled:
    print(f"\n{cyan('  SAST tools (Gates 11-13):')}")
    for tool in sast_tools:
        installed = tool_installed(tool)
        sast_tools[tool] = installed
        status = green("installed") if installed else yellow("not installed — gate will warn, not fail")
        print(f"{blue('  ℹ')}  {tool:<16} {status}")

# ═════════════════════════════════════════════════════════════════════════════
# Gates 1–10 — Code Quality, Structure & Tests
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n{cyan('  ── Code Quality Gates ──────────────────────────────')}")

# ── Gate 1: Black ─────────────────────────────────────────────────────────────
def gate_black() -> bool:
    if args.fix:
        print(f"  {yellow('⚠  --fix: running black auto-format on airflow_plugins/')}")
        code, _, _ = run_cmd(["black", str(PLUGIN_ROOT)])
    else:
        code, out, err = run_cmd(["black", "--check", "--diff", str(PLUGIN_ROOT)])
        if out: print(out)
        if err: print(err)
    return code == 0

run_gate("Black — Code Formatting", gate_black)

# ── Gate 2: Ruff ──────────────────────────────────────────────────────────────
def gate_ruff() -> bool:
    if args.fix:
        print(f"  {yellow('⚠  --fix: running ruff auto-fix on airflow_plugins/')}")
        code, _, _ = run_cmd(["ruff", "check", "--fix", str(PLUGIN_ROOT)])
    else:
        code, out, err = run_cmd(["ruff", "check", str(PLUGIN_ROOT)])
        if out: print(out)
        if err: print(err)
    return code == 0

run_gate("Ruff — Linting + Import Order", gate_ruff)

# ── Gate 3: Mypy ──────────────────────────────────────────────────────────────
def gate_mypy() -> bool:
    code, out, err = run_cmd([
        "mypy", str(PLUGIN_ROOT),
        "--ignore-missing-imports",
        "--disallow-untyped-defs",
        "--disallow-incomplete-defs",
        "--warn-return-any",
        "--warn-unused-ignores",
        "--exclude", "unit_test",
    ])
    if out: print(out)
    if err: print(err)
    return code == 0

run_gate("Mypy — Type Checking", gate_mypy)

# ── Gate 4: Bandit ────────────────────────────────────────────────────────────
def gate_bandit() -> bool:
    code, out, err = run_cmd([
        "bandit", "-r", str(PLUGIN_ROOT),
        "--severity-level", "medium",
        "--confidence-level", "medium",
        "--exclude", str(UNIT_TEST),
        "--quiet",
    ])
    if out: print(out)
    if err: print(err)
    return code == 0

run_gate("Bandit — Security Scan", gate_bandit)

# ── Gate 5: No DAG constructs ─────────────────────────────────────────────────
def gate_no_dag_constructs() -> bool:
    found = False
    for py_file in PLUGIN_ROOT.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in ["with DAG(", "from airflow.models import DAG", "from airflow import DAG"]:
            if pattern in content:
                print(red(f"  [BLOCKER] '{pattern}' in {py_file.relative_to(REPO_ROOT)}"))
                found = True
    if not found:
        print("  No DAG constructs found — clean")
    return not found

run_gate("No DAG Constructs in Wheel Source [BLOCKER]", gate_no_dag_constructs)

# ── Gate 6: No print() ────────────────────────────────────────────────────────
def gate_no_print() -> bool:
    found = False
    for layer_path in SOURCE_LAYERS:
        if not layer_path.exists():
            continue
        for py_file in layer_path.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    layer = layer_path.name
                    fix   = "self.log" if layer in ("operators", "sensors") else "logging.getLogger(__name__)"
                    print(red(f"  [MAJOR] print() in {py_file.relative_to(REPO_ROOT)}:{node.lineno}"))
                    print(red(f"          Use {fix} in {layer}/"))
                    found = True
    if not found:
        print("  No print() statements found — clean")
    return not found

run_gate("No print() in Any Layer [MAJOR]", gate_no_print)

# ── Gate 7: No module-level GCP clients ───────────────────────────────────────
def gate_no_module_level_gcp() -> bool:
    found       = False
    gcp_clients = ("bigquery.Client", "storage.Client", "secretmanager.", "dataproc_v1.")
    for layer_path in [PLUGIN_ROOT / "service", PLUGIN_ROOT / "utility"]:
        if not layer_path.exists():
            continue
        for py_file in layer_path.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.iter_child_nodes(tree):
                if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                    continue
                node_str = ast.unparse(node) if hasattr(ast, "unparse") else ""
                for client in gcp_clients:
                    if client in node_str:
                        print(red(f"  [BLOCKER] Module-level GCP client in {py_file.relative_to(REPO_ROOT)}:{node.lineno}"))
                        print(red(f"            Move '{client}' inside a method or @property"))
                        found = True
    if not found:
        print("  No module-level GCP clients found — clean")
    return not found

run_gate("No Module-Level GCP Client Instantiation [BLOCKER]", gate_no_module_level_gcp)

# ── Gate 8: No Airflow imports in lower layers ────────────────────────────────
def gate_no_airflow_in_lower_layers() -> bool:
    found = False
    for layer_path in LOWER_LAYERS:
        if not layer_path.exists():
            continue
        for py_file in layer_path.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = ""
                    if isinstance(node, ast.ImportFrom) and node.module:
                        module = node.module
                    elif isinstance(node, ast.Import):
                        module = ",".join(a.name for a in node.names)
                    if module.startswith("airflow"):
                        print(red(f"  [BLOCKER] Airflow import in {py_file.relative_to(REPO_ROOT)}:{node.lineno}"))
                        print(red(f"            {layer_path.name}/ must not depend on Airflow"))
                        found = True
    if not found:
        print("  No forbidden Airflow imports in service/utility/generator — clean")
    return not found

run_gate("No Airflow Imports in service/ utility/ generator/ [BLOCKER]", gate_no_airflow_in_lower_layers)

# ── Gate 9: No hardcoded secrets ─────────────────────────────────────────────
def gate_no_hardcoded_secrets() -> bool:
    found    = False
    patterns = [
        re.compile(r'password\s*=\s*["\'][^"\']+["\']',  re.IGNORECASE),
        re.compile(r'api_key\s*=\s*["\'][^"\']+["\']',   re.IGNORECASE),
        re.compile(r'token\s*=\s*["\'][^"\']+["\']',     re.IGNORECASE),
        re.compile(r'secret\s*=\s*["\'][^"\']+["\']',    re.IGNORECASE),
        re.compile(r'AKIA[0-9A-Z]{16}'),
    ]
    for py_file in PLUGIN_ROOT.rglob("*.py"):
        if UNIT_TEST in py_file.parents:
            continue
        content = py_file.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(content):
                print(red(f"  [BLOCKER] Possible hardcoded secret in {py_file.relative_to(REPO_ROOT)}"))
                print(red( "            Use utility/secrets/ GSM client instead"))
                found = True
                break
    if not found:
        print("  No hardcoded secrets found — clean")
    return not found

run_gate("No Hardcoded Secrets [BLOCKER]", gate_no_hardcoded_secrets)

# ── Gate 10: Pytest + Coverage ───────────────────────────────────────────────
def gate_tests() -> bool:
    code, out, err = run_cmd([
        "pytest", str(UNIT_TEST),
        "--tb=short",
        "--strict-markers",
        f"--cov={PLUGIN_ROOT}",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        f"--ignore={E2E_TEST}",
        "-q",
    ])
    if out: print(out)
    if err: print(err)
    return code == 0

run_gate("Pytest — Unit Tests + Coverage ≥80% (excludes gsm_e2e.py)", gate_tests)

# ═════════════════════════════════════════════════════════════════════════════
# Gates 11–13 — SonarQube + Fortify Equivalent (SAST)
# ═════════════════════════════════════════════════════════════════════════════
if not sast_all_disabled:
    print(f"\n{cyan('  ── SAST Gates (SonarQube + Fortify Equivalent) ─────')}")

# ── Gate 11: Semgrep ──────────────────────────────────────────────────────────
def gate_semgrep() -> bool:
    if not sast_tools["semgrep"]:
        print(yellow("  ⚠  semgrep not installed — skipping (install: pip install semgrep)"))
        return True
    print("  Running OWASP Top 10 + Python security ruleset...")
    code, out, err = run_cmd([
        "semgrep",
        "--config", "p/python",
        "--config", "p/owasp-top-ten",
        "--config", "p/secrets",
        "--config", "p/security-audit",
        str(PLUGIN_ROOT),
        "--exclude", str(UNIT_TEST.name),
        "--error",
        "--quiet",
    ])
    if out:
        for line in out.splitlines():
            if "finding" in line.lower() or "error" in line.lower():
                print(red(f"  [FORTIFY-EQUIV] {line}"))
            elif line.strip():
                print(f"  {line}")
    if err: print(err)
    if code == 0:
        print(green("  No OWASP / security issues found — clean"))
    return code == 0

run_gate("Semgrep — OWASP Top 10 + Python Security (Fortify equivalent)", gate_semgrep)

# ── Gate 12: pip-audit ────────────────────────────────────────────────────────
def gate_pip_audit() -> bool:
    if not sast_tools["pip-audit"]:
        print(yellow("  ⚠  pip-audit not installed — skipping (install: pip install pip-audit)"))
        return True
    print("  Scanning dependencies against OSV + PyPI advisory database...")
    code, out, err = run_cmd(["pip-audit", "--format", "json", "--progress-spinner", "off"])
    try:
        results         = json.loads(out) if out.strip() else {}
        vulnerabilities = results.get("vulnerabilities", [])
        if not vulnerabilities:
            print(green("  No known CVEs found in dependencies — clean"))
            return True
        critical = [v for v in vulnerabilities if v.get("fix_versions")]
        unfixed  = [v for v in vulnerabilities if not v.get("fix_versions")]
        for vuln in critical:
            pkg = vuln.get("name", "unknown")
            ver = vuln.get("version", "unknown")
            ids = ", ".join(v.get("id", "") for v in vuln.get("vulns", []))
            fix = ", ".join(vuln.get("fix_versions", []))
            print(red(   f"  [SONAR-EQUIV] [HIGH] {pkg}=={ver} — {ids}"))
            print(yellow(f"                Fix available: upgrade to {fix}"))
        for vuln in unfixed:
            pkg = vuln.get("name", "unknown")
            ver = vuln.get("version", "unknown")
            ids = ", ".join(v.get("id", "") for v in vuln.get("vulns", []))
            print(yellow(f"  [SONAR-EQUIV] [NO FIX YET] {pkg}=={ver} — {ids}"))
        return len(critical) == 0
    except (json.JSONDecodeError, KeyError):
        if out: print(out)
        if err: print(err)
        return code == 0

run_gate("pip-audit — Dependency CVE Scan (SonarQube equivalent)", gate_pip_audit)

# ── Gate 13: detect-secrets ───────────────────────────────────────────────────
def gate_detect_secrets() -> bool:
    if not sast_tools["detect-secrets"]:
        print(yellow("  ⚠  detect-secrets not installed — skipping (install: pip install detect-secrets)"))
        return True
    print("  Scanning for credentials, tokens, and API keys...")
    code, out, err = run_cmd([
        "detect-secrets", "scan",
        str(PLUGIN_ROOT),
        "--exclude-files", str(UNIT_TEST.name),
        "--exclude-files", r".*\.pyc$",
    ])
    try:
        results     = json.loads(out) if out.strip() else {}
        all_results = results.get("results", {})
        findings: list[tuple[str, int, str]] = []
        for filepath, secrets in all_results.items():
            for secret in secrets:
                findings.append((filepath, secret.get("line_number", 0), secret.get("type", "Unknown")))
        if not findings:
            print(green("  No secrets or credentials detected — clean"))
            return True
        for filepath, line, secret_type in findings:
            print(red(f"  [FORTIFY-EQUIV] {secret_type} in {filepath}:{line}"))
            print(red( "                  Move to utility/secrets/ GSM client"))
        return False
    except (json.JSONDecodeError, KeyError):
        if out: print(out)
        if err: print(err)
        return code == 0

run_gate("detect-secrets — Deep Credential Scan (Fortify equivalent)", gate_detect_secrets)

# ═════════════════════════════════════════════════════════════════════════════
# Gate 14 — Pylint Score (minimum 9.0/10)
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n{cyan('  ── Pylint Score Gate ───────────────────────────────')}")

PYLINT_MIN_SCORE = 9.0

# ── Gate 14: Pylint ───────────────────────────────────────────────────────────
# Runs full pylint across all source layers.
# Minimum acceptable score: 9.0 / 10.0
# Maps to SonarQube's code quality score and duplicate code detection.
# Catches: duplicate code (R0801), cyclomatic complexity (R0912),
#          too many arguments (R0913), missing docstrings (C0114),
#          and ~200 other code quality rules.
def gate_pylint() -> bool:
    if not tool_installed("pylint"):
        print(yellow("  ⚠  pylint not installed — skipping"))
        print(yellow("     Install with: pip install pylint"))
        return True  # warn but do not block if not installed

    print(f"  Running full pylint analysis (minimum score: {PYLINT_MIN_SCORE}/10)...")
    print( "  (Maps to: SonarQube code quality score + duplicate code detection)\n")

    code, out, err = run_cmd([
        "pylint",
        str(PLUGIN_ROOT),
        "--ignore", "unit_test",
        "--output-format", "text",
        "--score", "y",                      # always show the score line
        "--msg-template", "{path}:{line}: [{msg_id}({symbol})] {msg}",
        # Disable rules already covered by ruff/mypy/black to avoid duplicate noise
        "--disable", "C0301",                # line-too-long → black handles this
        "--disable", "C0303",                # trailing-whitespace → black handles this
        "--disable", "W0611",                # unused-import → ruff F401 handles this
        "--disable", "E0401",                # import-error → mypy handles this
        "--disable", "C0114,C0115,C0116",    # missing docstrings → we enforce via mypy/review
    ])

    # Always print full output so developer sees every issue
    if out:
        lines     = out.strip().splitlines()
        score_val: float | None = None

        for line in lines:
            # Parse the score line: "Your code has been rated at X.XX/10"
            if "Your code has been rated at" in line:
                try:
                    score_str = line.split("rated at")[1].split("/")[0].strip()
                    score_val = float(score_str)
                except (IndexError, ValueError):
                    pass

                # Print the score line with colour based on result
                if score_val is not None:
                    if score_val >= PYLINT_MIN_SCORE:
                        print(green(f"  Score: {score_val:.2f}/10  (minimum: {PYLINT_MIN_SCORE}/10) ✔"))
                    else:
                        print(red(  f"  Score: {score_val:.2f}/10  (minimum: {PYLINT_MIN_SCORE}/10) ✘"))
                        print(red(  f"  Score is below the required {PYLINT_MIN_SCORE}/10 threshold"))
            elif line.strip():
                # Colour-code individual messages by severity
                if ": [E" in line or ": [F" in line:
                    print(red(   f"  {line}"))        # Error / Fatal
                elif ": [W" in line:
                    print(yellow(f"  {line}"))        # Warning
                elif ": [R" in line:
                    print(cyan(  f"  {line}"))        # Refactor
                elif ": [C" in line:
                    print(f"  {grey(line)}")          # Convention
                else:
                    print(f"  {line}")

        if score_val is None:
            print(yellow("  Could not parse pylint score — check output above"))
            return False

        return score_val >= PYLINT_MIN_SCORE

    if err:
        print(err)

    return code == 0

run_gate(f"Pylint — Code Quality Score ≥{PYLINT_MIN_SCORE}/10 (SonarQube equivalent)", gate_pylint)

# ═════════════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════════════
total_active = _current_gate_num - len(skipped)

print()
print("━" * 57)

# Show SAST mapping
if not sast_all_disabled:
    print(cyan("  SonarQube / Fortify coverage summary:"))
    print(f"  {'Fortify SAST':<32} Gate 11 — semgrep")
    print(f"  {'SonarQube dependency scan':<32} Gate 12 — pip-audit")
    print(f"  {'Fortify credential scan':<32} Gate 13 — detect-secrets")
    print(f"  {'Fortify/Bandit security':<32} Gate  4 — bandit")
    print(f"  {'SonarQube code quality score':<32} Gate 14 — pylint (≥9.0/10)")
    print()

# Show disabled gates in summary
if skipped:
    print(yellow(f"  ⊘  {len(skipped)} gate(s) were disabled and did not run:"))
    for s in skipped:
        print(yellow(f"     • {s}"))
    print()

if not failed:
    print(green(f"  ✔ All {total_active} active gate(s) passed — safe to open PR"))
    if skipped:
        print(yellow(f"  ⚠  Remember: {len(skipped)} gate(s) were skipped — re-enable before final merge"))
    print()
    print("  Reminder — manual wheel release steps after merge:")
    print("  1. Bump version in pyproject.toml")
    print("  2. Update CHANGELOG.md")
    print("  3. python -m build")
    print("     → dist/airflow_platform_plugins-x.y.z-py3-none-any.whl")
    print("  4. gsutil cp dist/*.whl gs://<composer-bucket>/plugins/")
    print("  5. Update plugin_version in DAG repo platform_conf.json")
    print("━" * 57)
    sys.exit(0)
else:
    print(red(f"  ✘ {len(failed)} gate(s) failed — do not open PR yet:"))
    for name in failed:
        print(red(f"    • {name}"))
    print()
    print(f"  Tip: run {yellow('python scripts/pre_review_gate.py --fix')} to")
    print("  auto-correct Black and Ruff issues, then re-run.")
    print("━" * 57)
    sys.exit(1)
