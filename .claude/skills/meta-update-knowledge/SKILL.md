---
name: meta-update-knowledge
description: Update project knowledge base after a session (create or update .claude/knowledge/*.md files)
---

Review the current conversation and update project knowledge.

The knowledge base is an **architectural reference**, not a session log or changelog. Its purpose is to capture things that can't be derived from reading the code or git history.

## Steps

1. Read `CLAUDE.md` to see the knowledge table and existing file list
2. Read all files in `.claude/knowledge/` to understand what's already documented
3. Review the conversation and recent git diff to understand what happened
4. Update knowledge:
   - **Existing file needs update**: edit the relevant `.md` in `.claude/knowledge/`
   - **New feature/topic**: create a new `.md` in `.claude/knowledge/` and add a row to the Knowledge table in `CLAUDE.md`
   - **General pattern discovered**: add to `CLAUDE.md` directly (not knowledge files)
5. **Cleanup pass**: check all existing knowledge files for stale content - references to removed features, deprecated approaches, or details that are now irrelevant. Trim or delete as needed.
6. If `CLAUDE.md` general sections need updates (new commands, env vars, architecture changes), update them too

## What to save

Only save things that **the code and git history don't already tell you**:

- **Why**: rationale behind design choices, why approach A was picked over B
- **Gotchas**: non-obvious behaviors, silent failures, tricky edge cases discovered during implementation
- **Constraints**: external factors that shaped the design (API limitations, infrastructure constraints, business rules)
- **How components connect**: relationships and data flows that aren't obvious from the code structure alone
- **How-to**: setup steps, deployment quirks, or operational knowledge that isn't documented elsewhere

## What NOT to save

The code is the source of truth for implementation details. Don't duplicate it:

- What files were changed or created (git knows this)
- Current state of a feature's implementation (the code shows this)
- Config values, function signatures, or data structures (read the code)
- Step-by-step logs of what was done in a session
- Approaches that were tried and abandoned (unless the failure is genuinely instructive for future work)
- Deprecated or removed features (delete these from knowledge files)

## Rules

- **Write ONLY to `.claude/knowledge/` in the repo. NEVER to `~/.claude/projects/*/memory/`.**
- Be concise. Every token costs money and context space.
- No fluff, no redundancy with CLAUDE.md.
- Knowledge files are feature-specific and evolving. CLAUDE.md is general and stable.
- Use explicit filenames that describe the feature (e.g. `boss-pipeline.md`, `bofip-pipeline.md`).
- Apply the **3-month test**: "Would this help someone understand the system 3 months from now?" If not, cut it.
