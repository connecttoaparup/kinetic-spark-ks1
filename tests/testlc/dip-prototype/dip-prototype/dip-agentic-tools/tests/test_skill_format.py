#!/usr/bin/env python3
"""CI gate: validate every SKILL.md against the Agent Skills spec.
Pure stdlib (no pyyaml) - parses simple frontmatter key: value / block scalars.
Checks: frontmatter present, name present+valid+matches dir, description
present+<=1024, file <=500 lines, and GLOBAL name uniqueness (flat-install)."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # dip-agentic-tools/
SKILLS_ROOT = HERE / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME, MAX_DESC, MAX_LINES = 64, 1024, 500


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("unterminated frontmatter")
    fm: dict = {}
    key = None
    for raw in text[3:end].splitlines():
        if not raw.strip():
            continue
        if raw.startswith((" ", "\t")):                 # continuation / nested
            if key:
                fm[key] = (fm.get(key, "") + " " + raw.strip()).strip()
            continue
        if ":" in raw:
            key, _, val = raw.partition(":")
            key = key.strip()
            val = val.strip()
            fm[key] = "" if val in (">", "|", ">-", "|-") else val
    return fm


def check(md: Path) -> list[str]:
    errs, text, d = [], md.read_text(encoding="utf-8"), md.parent.name
    try:
        fm = parse_frontmatter(text)
    except Exception as ex:
        return [f"{md.relative_to(HERE)}: {ex}"]
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not name:
        errs.append(f"{md.relative_to(HERE)}: missing name")
    else:
        if len(name) > MAX_NAME:
            errs.append(f"{md.relative_to(HERE)}: name >{MAX_NAME} chars")
        if not NAME_RE.match(name):
            errs.append(f"{md.relative_to(HERE)}: name must be lowercase/hyphens")
        if name != d:
            errs.append(f"{md.relative_to(HERE)}: name '{name}' != dir '{d}'")
    if not desc:
        errs.append(f"{md.relative_to(HERE)}: missing description")
    elif len(desc) > MAX_DESC:
        errs.append(f"{md.relative_to(HERE)}: description >{MAX_DESC} chars")
    if text.count("\n") > MAX_LINES:
        errs.append(f"{md.relative_to(HERE)}: >{MAX_LINES} lines")
    return errs


def main() -> int:
    skills = sorted(SKILLS_ROOT.rglob("SKILL.md"))
    if not skills:
        print("No SKILL.md found.")
        return 1
    errs: list[str] = []
    names: dict[str, Path] = {}
    for s in skills:
        errs += check(s)
        try:
            n = parse_frontmatter(s.read_text(encoding="utf-8")).get("name")
            if n in names:
                errs.append(f"{s.relative_to(HERE)}: duplicate name '{n}' "
                            f"(also {names[n].relative_to(HERE)})")
            elif n:
                names[n] = s
        except Exception:
            pass
    if errs:
        print("SKILL VALIDATION FAILED:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(skills)} skills valid, names globally unique.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
