---
name: review-deep
description: Deep structural review of a pull request. Use when the user runs /review-deep, /review-deep <number>, or /review-deep focus <area>.
---

# review-deep

AI-generated code passes every surface check by default -- clean syntax, good formatting, type-correct, tests green. This review deliberately ignores all of that. It exists to force comprehension of the change in system context, not to evaluate it against a style guide or catch bugs a linter would find.

The review must demonstrate that the reviewer understands what the code does, how it fits the existing system, and what it assumes. If it can't, that is the primary finding.

## Commands

| Invocation | Behavior |
|---|---|
| `/review-deep` | Review the current branch's PR (auto-detected via `gh pr view`) |
| `/review-deep <number-or-url>` | Review a specific PR by number or GitHub URL |
| `/review-deep focus <pass>` | Run a single pass: `comprehension`, `architecture`, `duplication`, `assumptions`, or `maintainability` |

There is no quick mode. Quick reviews are the problem this skill exists to solve.

## How to fetch PR data

```bash
# Resolve PR number (current branch or explicit)
PR_NUMBER=$(gh pr view --json number --jq '.number')  # or use the provided number

# PR metadata and description
gh pr view $PR_NUMBER --json title,body,baseRefName,headRefName,files,additions,deletions,author,labels

# Full diff
gh pr diff $PR_NUMBER

# Changed file paths
gh pr view $PR_NUMBER --json files --jq '.files[].path'

# Comments and review threads (for context on existing discussion)
gh pr view $PR_NUMBER --json comments,reviews
```

## Review protocol

Five sequential passes. Each builds context for the next. Do not skip or reorder.

### Pass 1: Comprehension

**Question: "What does this change actually do?"**

Before evaluating anything, produce a plain-language summary of what the PR does in terms of **system behavior**, not files changed. This forces reading surrounding code, not just the diff.

Steps:
1. Read the PR description and full diff
2. For each significantly changed file, read the **full file** (not just the diff hunk) to understand the surrounding context
3. Read files that import or are imported by the changed files
4. Produce a summary that references existing components by name and explains how they interact with the new code

If you cannot produce this summary -- if the change is opaque even after reading the surrounding code -- stop here. That inability is itself the most important finding. State what you could not understand and why.

### Pass 2: Architectural alignment

**Question: "Does this fit how the system was designed?"**

Steps:
1. Read `CLAUDE.md` and any `.claude/knowledge/*.md` files in the repo
2. Compare the PR's approach against documented patterns and conventions
3. Look for:
   - New patterns that diverge from established ones (e.g. a new way to handle errors when a convention already exists)
   - Data flowing through unexpected paths
   - Responsibilities landing in the wrong layer
   - New dependencies that create coupling the architecture was designed to avoid
4. If no architectural documentation exists, infer patterns from the existing code structure and flag the absence as a secondary finding

### Pass 3: Silent duplication

**Question: "Does this reinvent something that already exists?"**

AI-generated code is particularly prone to reimplementing existing functionality because the model may not have seen the full codebase when generating the code.

Steps:
1. For each new function, class, or module introduced in the PR, grep the codebase for:
   - Similar names
   - Similar function signatures
   - Similar string literals or constants
2. Read the imports of changed files to understand what utilities are already available
3. Flag **semantic duplicates** (different implementation, same purpose) -- not just name collisions

### Pass 4: Hidden assumptions

**Question: "What does this code assume that isn't stated?"**

Identify implicit contracts the code relies on:
- Ordering guarantees (this runs after that)
- Data shape assumptions (this field is always present, always non-null)
- Environment expectations (this env var exists, this service is reachable)
- Timing dependencies (this completes before that starts)
- Error propagation assumptions (this will never fail; if it does, the caller handles it)
- State assumptions (this has already been initialized, this lock is held)

The key question: **"Under what conditions would this code silently produce wrong results instead of failing loudly?"**

Check specifically for:
- Missing input validation at system boundaries
- Hardcoded values that encode environment assumptions
- Database queries that assume indexes exist or columns are non-null
- Error paths that swallow failures or return defaults instead of propagating

### Pass 5: Future maintainability

**Question: "What would a new maintainer need to know in 3 months?"**

Steps:
1. Check for non-obvious control flow or implicit ordering between functions
2. Look for magic numbers or strings without explanation
3. Identify knowledge that exists only in the PR description but not in the code or documentation
4. Check whether new configuration options or error messages are documented and specific enough to diagnose problems without reading the source
5. Flag context that should be preserved in code comments or docs but currently isn't

## Output format

Structure the review exactly as follows. Each section either has findings or a brief "nothing found" statement. No filler.

```
## Comprehension

[Plain-language summary of what the change does in system terms.
References specific existing components and how they interact with the new code.]

## Architectural alignment

[Findings with references to the established pattern and how the PR departs from it.
Or: "No divergence found."]

## Duplication

[Findings with references to existing code that overlaps.
Or: "No duplication found."]

## Hidden assumptions

[Each assumption stated explicitly, with the condition under which it would break.
Or: "No hidden assumptions found."]

## Maintainability

[Findings about what would confuse a future reader.
Or: "No concerns."]

---

Questions for the author:
1. [Things that could not be determined from the code alone]
2. [Ambiguities that require the author's intent to resolve]
```

The "Questions for the author" section is not optional. Frame ambiguities as questions rather than judgments -- the reviewer may be wrong, and the question lets the author clarify. If there are genuinely no questions, write "None" -- but that should be rare.

No merge recommendation. No overall score. No severity ratings. The output is findings and questions, not a verdict. The human decides what matters.

## What this review must NOT do

These anti-patterns are easy to fall into. Resist them explicitly:

- **Do not comment on formatting, naming, or style.** That is what linters and formatters are for.
- **Do not flag type-level or lint-level issues.** CI handles those. If CI is broken, that's a separate problem.
- **Do not suggest "add more tests" generically.** If test coverage matters, specify exactly what behavior is untested and why that gap is dangerous. Otherwise say nothing.
- **Do not produce a merge/no-merge recommendation.** The review surfaces information. The human makes the call.
- **Do not praise code quality.** The review is structurally adversarial -- its job is to find what's wrong or unclear, not to validate.
- **Do not review the PR description's writing quality.** Review the code.
- **Do not invent concerns.** If a pass genuinely turns up nothing, say so and move on. Padding the review with speculative issues undermines trust in the real findings.
