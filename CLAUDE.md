# Shared Claude instructions

This file contains shared instructions for Claude Code across projects.

## Skills

Check `.claude/skills/` for available skill definitions. Skills provide Claude with instructions for specific tasks such as database access, API interaction, or workflow automation.

### Naming convention

Skill names use a category prefix so the list groups by purpose:

- `utils-*` — reusable helpers (e.g. `utils-db-query`, `utils-notion`)
- `review-*` — PR/branch analysis (e.g. `review-deep`, `review-tech-debt`)
- `meta-*` — skill and config plumbing (e.g. `meta-sync-skills`)

The convention mirrors Wiseclerk's skills repo. New skills should pick the category that best fits their purpose; add a new prefix only when none of the existing ones apply.
