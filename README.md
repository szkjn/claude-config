# claude-config

Shared Claude configuration and skills across repositories.

## Structure

- `CLAUDE.md` — shared instructions for Claude Code
- `.claude/skills/` — shared skill definitions (`.md` files)
- `scripts/` — shared scripts used by skills

## Directory structure convention

Symlinks in child repos use relative paths, so **all repos must be cloned under the same parent directory**:

```
~/Code/
├── claude-config/        # this repo
│   └── .claude/
│       └── skills/
│           ├── db-query.md
│           └── es-search.md
├── wisepipe/
│   └── .claude/
│       └── skills/
│           ├── db-query.md -> ../../../claude-config/.claude/skills/db-query.md
│           ├── es-search.md -> ../../../claude-config/.claude/skills/es-search.md
│           └── s3-access.md  (project-specific, not symlinked)
├── wisebrain/
│   └── .claude/
│       └── skills/
│           └── es-search.md -> ../../../claude-config/.claude/skills/es-search.md
└── wisetax-app/
    └── .claude/
        └── skills/
            └── es-search.md -> ../../../claude-config/.claude/skills/es-search.md
```

Both team members must clone `claude-config` to `~/Code/claude-config` (or adjust the parent path consistently).

## Adding a shared skill to a repo

```bash
ln -s ../../../claude-config/.claude/skills/SKILL.md .claude/skills/SKILL.md
```
