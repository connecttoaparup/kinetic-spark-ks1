#!/usr/bin/env python3
"""Install DIP skills to the personal scope (~/.copilot/skills) - the same
flat, name-unique install layout `gh skill install` produces. At work you
would run instead:
  gh skill install <org>/dip-agentic-tools --path skills --pin v1.0.0
"""
import shutil
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "dip-agentic-tools" / "skills"
DST = Path.home() / ".copilot" / "skills"
DST.mkdir(parents=True, exist_ok=True)

installed = []
for skill_md in sorted(SRC.rglob("SKILL.md")):
    leaf = skill_md.parent
    target = DST / leaf.name          # FLAT install - names are globally unique
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(leaf, target)
    installed.append(leaf.name)
print(f"Installed {len(installed)} skills to {DST}:")
for n in installed:
    print(f"  - {n}")
print("\nRestart VS Code (or Reload Window) so Copilot re-discovers skills.")
