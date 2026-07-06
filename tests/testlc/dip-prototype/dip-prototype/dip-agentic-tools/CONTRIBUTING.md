# Contributing (Prototype)

1. New skill: copy templates/skill-template.md into skills/<bucket>/<name>/SKILL.md.
   The `name:` field MUST equal the directory name (lowercase, hyphens).
2. Run the CI gate locally: `python tests/test_skill_format.py`.
3. Skill names must be GLOBALLY unique across all buckets (flat-install safety).
