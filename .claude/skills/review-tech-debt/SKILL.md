---
name: review-tech-debt
description: Check whether the current branch introduces technical debt. Use when the user runs /review-tech-debt or /review-tech-debt focus <area>.
---

# review-tech-debt

Check whether the current branch adds technical debt to the codebase. Operates on the full branch diff (all commits since diverging from the base branch), not a single commit or staged changes.

This is a different lens from review-deep. Review-deep asks "is this change correct and comprehensible?" This skill asks "is this change sustainable?" A perfectly correct, well-understood change can still introduce a second way to do the same thing, stop a migration halfway, or add abstraction nobody asked for.

## Commands

| Invocation | Behavior |
|---|---|
| `/review-tech-debt` | Check the current branch for debt introduction |
| `/review-tech-debt focus <check>` | Run a single check: `conventions`, `migrations`, `duplication`, `complexity`, or `markers` |

## How to get the diff

```bash
# Detect base branch (adjust if default branch is not main/master)
BASE=$(git merge-base HEAD main)

# Full diff
git diff $BASE...HEAD

# Changed files
git diff $BASE...HEAD --name-only

# Stat summary
git diff $BASE...HEAD --stat
```

## Debt checks

Five sequential checks. Each looks for a specific category of debt. Read the full diff first to understand the changes, then proceed through each check.

### 1. Convention drift

**Question: "Does this introduce a new way to do something that already has an established pattern?"**

Steps:
1. Read `CLAUDE.md` and any `.claude/knowledge/*.md` files for documented conventions
2. For each changed file, read surrounding code in the same module to identify the established patterns
3. Look for:
   - New error handling approaches where a convention already exists
   - New state management or data access patterns
   - New API call patterns (HTTP clients, retry logic, auth handling)
   - New logging or observability patterns
   - New config access patterns

The question is not "is the new way better?" It's "now there are two ways, and nobody will know which to use."

### 2. Incomplete migrations

**Question: "Does this leave old and new coexisting?"**

When the branch introduces a new pattern or refactors an existing one, check whether the old pattern still exists elsewhere in the codebase.

Look for:
- Partial renames (some files updated, some not)
- New utility introduced but the old inline version still used in untouched files
- New API or interface used in changed files but the old one still called elsewhere
- Import path changes applied in some places but not others

The debt is not the migration itself. It's stopping halfway. Two coexisting patterns are worse than either one alone.

### 3. Copy-paste duplication

**Question: "Does this duplicate logic that exists elsewhere?"**

Steps:
1. For each new function, class, or module, grep the codebase for similar names, signatures, or string literals
2. Read imports of changed files to understand what utilities are already available
3. Distinguish between:
   - Exact duplication (copied code)
   - Near-duplication (same logic, different variable names)
   - Semantic duplication (different implementation, same purpose)

**Before flagging duplication, apply these criteria to decide if it warrants a fix:**

Flag duplication when:
- The duplicates are in the **same call chain** or module boundary (one calls the other, or both serve the same request path) -- the data is already available, recomputing it is waste
- The duplicates share a **single reason to change** -- when the logic changes, forgetting to update both is a bug
- A shared helper would be **simple** (a small function, a field on an existing return type) -- not a new abstraction layer

Leave duplication alone when:
- The duplicates live in **different layers** with different consumers (e.g., one feeds an LLM prompt, the other feeds a frontend UI) -- merging would couple things that change for different reasons
- The data shape is **superficially similar but semantically different** (e.g., same codes but different metadata: descriptions vs. display groups)
- Deduplicating would require a **new abstraction** that adds more complexity than the duplication itself
- The duplicated code is **stable and changes infrequently** -- the maintenance cost of two copies is low

Only report duplication that passes these criteria. For borderline cases, state the tradeoff and let the author decide.

### 4. Unjustified complexity

**Question: "Does the complexity serve the current use case, or is it speculative?"**

Look for:
- Configuration for things that have only one value
- Interfaces or abstractions with only one implementation
- Feature flags that gate unreleased or unfinished code
- Layers of indirection that don't provide meaningful separation
- Generic solutions to specific problems (a framework where a function would do)

This is not about code length. A 50-line function can be simpler than a 3-class hierarchy that does the same thing.

### 5. Explicit debt markers

**Question: "Does this acknowledge debt it's creating?"**

Scan the diff for: TODO, FIXME, HACK, XXX, "temporary", "workaround", "tech debt", "revisit".

This is not about punishing the author. Marking debt explicitly is good practice. The check surfaces these so the author can decide: is this intentional and tracked, or did it slip in?

For each marker found:
- Does it have enough context to act on later? A bare `// TODO` with no explanation is worse than no TODO at all.
- Is there a ticket or issue reference? If not, the debt is invisible to project management.
- Is the scope clear? "TODO: fix this" is not actionable. "TODO: migrate to bulk insert once the batch API supports > 1000 rows" is.

## Output format

```
## Convention drift

[What the established pattern is, what the branch introduces instead,
and where they now coexist. Or: "No new conventions introduced."]

## Incomplete migrations

[What was partially migrated, what remains on the old pattern.
Or: "No partial migrations found."]

## Duplication

[What was duplicated, where the original lives.
Or: "No duplication found."]

## Complexity

[What abstraction or indirection isn't justified by current use.
Or: "No unjustified complexity found."]

## Debt markers

[List of explicit TODO/FIXME/HACK markers in the diff, with assessment
of whether each has sufficient context. Or: "No markers found."]

---

Debt tradeoffs to discuss:
1. [Items where adding debt may be the right call, but should be a conscious decision]
```

The closing section is "Debt tradeoffs to discuss." Debt is often intentional -- shipping faster, deferring a migration to a dedicated PR, keeping scope small. The skill makes the tradeoff visible so the author decides consciously, not accidentally.

No severity scores. No aggregate rating. No debt-to-equity ratio.

## What this check must NOT do

- **Do not flag formatting, naming, or style.** Those are not debt.
- **Do not flag missing tests generically.** Missing test coverage is only debt if a specific behavior is both critical and untested. Say which behavior and why.
- **Do not flag "code smells" by name** (e.g., "this is a God class"). Describe the actual cost: "this module handles both X and Y, which means changing X requires understanding Y."
- **Do not recommend refactoring without stating what it costs to leave it.** "This could be cleaner" is not a debt finding. "This means every new endpoint will need to duplicate these 15 lines" is.
- **Do not treat all debt as bad.** Some debt is the right tradeoff. The skill surfaces it; the human decides.
- **Do not invent concerns.** If a check turns up nothing, say so and move on. Speculative debt findings erode trust in the real ones.
