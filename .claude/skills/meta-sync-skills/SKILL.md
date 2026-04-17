---
name: meta-sync-skills
description: Check and sync symlinks from claude-config shared skills into the current repo. Use when the user runs /meta-sync-skills.
---

# meta-sync-skills

Ensures the current repository has symlinks to all relevant shared skills from `claude-config`.

## How it works

1. **Locate claude-config**: resolve the path by following an existing symlink in `.claude/skills/` back to claude-config's skills directory. If no symlink exists yet, fall back to `~/Code/claude-config`.
2. **Inventory claude-config skills**: list all skill directories in `claude-config/.claude/skills/` (exclude `.gitkeep` and this skill itself -- `meta-sync-skills` should never be symlinked to itself).
3. **Inventory current repo**: list all entries in the current repo's `.claude/skills/`, noting which are symlinks (and where they point) vs local directories.
4. **Detect issues**:
   - **Missing**: claude-config skills with no corresponding entry in the current repo
   - **Broken**: symlinks that point to a target that no longer exists
5. **Report**: print a clear summary table showing each claude-config skill and its status in the current repo (linked / missing / broken).
6. **Act**: for each missing skill, ask the user whether to create a symlink. Create symlinks using **absolute paths** (e.g. `/Users/junsuzuki/Code/claude-config/.claude/skills/review-brain-check`). For broken symlinks, ask the user whether to remove them.

## Rules

- **Never run inside `claude-config` itself.** If the working directory IS claude-config, print a message and stop: "This skill is meant to be run from a consuming repo, not from claude-config itself."
- **Never overwrite local (non-symlink) skill directories.** If a skill name exists as a real directory in the current repo, skip it -- the repo has its own version.
- **Never symlink `meta-sync-skills` to itself.** Exclude it from the inventory.
- **Always create `.claude/skills/` if it doesn't exist** before creating symlinks.
- **Use `ln -s` with absolute paths** for portability across shell sessions.
- **After creating symlinks**, remind the user to register new skills in their `settings.json` or `CLAUDE.md` if required by their setup.
