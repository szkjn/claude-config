---
name: review-brain-check
description: Take a brain check -- interactive comprehension quiz on a PR or branch. Use when the user runs /review-brain-check or /review-brain-check <number>.
---

# review-brain-check

review-deep tests whether Claude comprehends a PR. This skill tests whether the human does. Claude reads the diff, builds understanding silently, then asks the user targeted questions that test whether they can explain what the change does, why, and what happens when things go wrong.

No code changes. No documentation writes. No scores. Just a forcing function for the human to demonstrate they understand what they're about to ship.

## Commands

| Invocation | Behavior |
|---|---|
| `/review-brain-check` | Quiz on the current branch's PR (auto-detected via `gh pr view`) |
| `/review-brain-check <number-or-url>` | Quiz on a specific PR |

No `focus` subcommand. The skill tests holistic understanding, not knowledge of a specific file.

## How to fetch PR data

```bash
# Resolve PR number
PR_NUMBER=$(gh pr view --json number --jq '.number')  # or use the provided number

# PR metadata and description
gh pr view $PR_NUMBER --json title,body,baseRefName,headRefName,files,additions,deletions,author,labels

# Full diff
gh pr diff $PR_NUMBER

# Changed file paths
gh pr view $PR_NUMBER --json files --jq '.files[].path'
```

## Protocol

Three phases. The first is silent -- the user sees only phases 2 and 3.

### Phase 1: Silent analysis

Do not show this to the user. Build understanding internally.

1. Fetch the PR metadata and full diff
2. For each significantly changed file, read the **full file** to understand surrounding context
3. Read files that import or are imported by the changed files
4. Read `CLAUDE.md` and any `.claude/knowledge/*.md` files for architectural context
5. Identify:
   - The behavioral changes (what the system does differently after this PR)
   - The failure modes (what happens when dependencies fail, inputs are unexpected, state is inconsistent)
   - The interaction effects (how this affects components the PR didn't touch)
   - The design decisions (why this approach over alternatives)
   - The load-bearing parts (where misunderstanding has real consequences)

### Phase 2: Questions

Generate **3 to 5 questions**. No more. Quality over quantity.

Present them all at once. Let the user answer in a single response.

**Question requirements:**

- **Target behavioral changes, not implementation details.** Ask "What happens to in-flight requests when the retry logic kicks in?" -- not "What does line 42 do?"
- **Focus on the non-obvious.** Edge cases, failure modes, interactions with components the PR didn't touch. Don't ask about things that are self-evident from the diff.
- **Be specific enough that a generic answer reveals lack of understanding.** "It handles errors" is insufficient. The question should require the user to demonstrate they know *how* errors are handled and *what happens* when they are.
- **Cover the "why", not just the "what".** "Why was polling chosen over websockets here?" tests whether the user understood the constraint that shaped the decision.
- **Target the load-bearing parts.** Not every change matters equally. Focus on the parts where misunderstanding has real consequences -- auth flows, data mutations, payment paths, error propagation, concurrency.

**Question categories** (draw from these, don't use all every time):

1. **Behavioral impact**: "What does the user experience differently after this change?"
2. **Failure modes**: "What happens if [dependency] is unavailable or returns unexpected data?"
3. **Interaction effects**: "How does this affect [component that wasn't modified but depends on this code]?"
4. **Design rationale**: "Why [approach X] over [obvious alternative Y]?"
5. **Boundary conditions**: "What's the expected behavior when [edge case]?"

**Output format for this phase:**

```
I've read through PR #123. Before you merge, walk me through a few things:

1. [Question]
2. [Question]
3. [Question]

Take your time. Answer in your own words.
```

Keep it conversational. Not an exam.

### Phase 3: Gap analysis

After the user answers, analyze their responses. Then output:

```
## What you clearly understand

[Brief summary of areas where the user's answers demonstrate solid comprehension.
Be specific -- reference the parts of their answers that showed real understanding.]

## Gaps worth closing

[For each gap identified:
- What the user said (or didn't say)
- What the code actually does
- A pointer to the specific code (file:line or function name)
Keep this constructive. The goal is to close gaps, not to catch the user out.]

## Suggested follow-up

[1-2 specific things the user could read or verify to close the gaps.
Not "read the whole file" -- specific functions, specific flows, specific
interactions to trace.]
```

If the user's answers demonstrate solid comprehension across the board, say so clearly and keep the output short. Don't manufacture gaps to justify the skill's existence.

## What this skill must NOT do

- **Do not ask trivial questions.** "What language is this?" or "Which files changed?" wastes the user's time and insults their intelligence.
- **Do not ask questions answerable from the PR description alone.** The point is to test understanding of the code, not reading comprehension of the summary.
- **Do not ask more than 5 questions.** More than that turns this into a chore that gets skipped. If 3 questions cover it, stop at 3.
- **Do not grade or score.** No "you got 3/5." The feedback is collaborative, not evaluative.
- **Do not be condescending.** The user is a professional. "You might want to look at..." -- not "You failed to understand..."
- **Do not write any files.** No code changes, no documentation, no knowledge files. This skill is strictly read-only plus conversation.
- **Do not repeat the diff back to the user.** They already read it. Ask about it, don't recite it.
- **Do not manufacture gaps.** If the user understands the change, say so. Inventing concerns to look thorough undermines trust.
