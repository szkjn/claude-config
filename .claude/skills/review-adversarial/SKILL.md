---
name: review-adversarial
description: Adversarial review of a proposed solution. Spawns two independent subagents to debate the approach and surface blind spots. Use when the user runs /review-adversarial.
---

# review-adversarial

When the current conversation contains a proposed solution (from you or from another agent), this skill spins up two subagents with opposing mandates to stress-test it. The goal is to surface blind spots, unstated assumptions, and better alternatives that a single perspective misses.

## Invocation

| Command | Behavior |
|---|---|
| `/review-adversarial` | Debate the most recent proposed solution in the conversation |
| `/review-adversarial <context>` | Debate with additional framing or focus area |

## Protocol

### Step 0: Prepare the brief

Before spawning agents, write a self-contained brief that includes:

1. **The problem**: what issue is being solved and why
2. **The proposed solution**: what was suggested, by whom (you or another agent), and the reasoning behind it
3. **Relevant code context**: file paths, line numbers, key snippets -- enough for the agents to form an independent opinion without needing to re-discover everything
4. **Constraints**: any non-negotiable requirements (performance, backwards compatibility, etc.)

This brief must be complete enough that an agent with zero conversation history can reason about the problem. Do not say "the proposed solution" without describing it. Do not reference "the file we looked at" without naming it.

### Step 1: Independent analysis (parallel)

Spawn two agents **in parallel** using the Agent tool:

**Agent Advocate**
- Mandate: steelman the proposed solution
- Must explain *why* the solution is correct, what problems it solves, and what alternatives it's better than
- Must identify the weakest points in its own position
- Role framing in prompt: "You are reviewing a proposed solution. Your job is to argue FOR it -- explain why it's the right approach, what it gets right, and why alternatives would be worse. Also identify the weakest points in your own argument."

**Agent Challenger**
- Mandate: find flaws, blind spots, and better alternatives
- Must propose at least one concrete alternative (not just critique)
- Must acknowledge what the proposed solution gets right
- Role framing in prompt: "You are reviewing a proposed solution. Your job is to argue AGAINST it -- find flaws, unstated assumptions, edge cases, and unnecessary complexity. You must propose at least one concrete alternative. Also acknowledge what the current proposal gets right."

Both agents receive the identical brief from Step 0. Both should read relevant source files themselves to form grounded opinions.

### Step 2: Rebuttal (parallel)

Send each agent the other's analysis via SendMessage:

- Send Advocate the Challenger's analysis: "Here is the opposing view. Respond to their strongest points. Where are they right? Where are they wrong? Have they changed your position at all?"
- Send Challenger the Advocate's analysis: "Here is the defense. Respond to their strongest points. Where are they right? Where are they wrong? Have they changed your position at all?"

### Step 3: Final positions (parallel)

One more round via SendMessage to each:

- "Final position. In under 150 words: state your recommendation and the single strongest argument for it. Flag any remaining disagreement as an open question for the user."

### Step 4: Synthesis

You (the orchestrating agent) read both final positions and produce the output. Do NOT delegate synthesis to a subagent -- you have the full conversation context they lack.

## Output format

```
## Problem

[One-paragraph summary]

## Proposed solution

[What was proposed and why]

## Debate summary

### Points of agreement
- [What both agents agreed on]

### Key disagreements
- [Where they diverged, with each side's strongest argument]

### Blind spots surfaced
- [Things neither the original proposal nor the initial conversation considered]

## Recommendation

[Your synthesis -- not a vote count, but a reasoned position informed by both perspectives.
State clearly what you'd do and why. Flag open questions the user should weigh in on.]
```

## Constraints

- Maximum 3 rounds of exchange (independent analysis, rebuttal, final position). Do not let the debate run longer -- diminishing returns set in fast.
- Each agent response should be capped at ~300 words per round. Instruct them accordingly.
- The two agents must never see each other's analysis in round 1. Independence is the whole point.
- If both agents agree on everything after round 1, skip rounds 2-3 and report the consensus. Artificial disagreement is worse than none.
- Keep the final synthesis concise. The user has been in this conversation -- they don't need a recap of everything they already know. Focus on what's new.

## What this skill is NOT

- Not a code review (use `/review-deep` for that)
- Not a rubber stamp -- if the proposed solution is actually fine, the debate should surface that quickly and end early
- Not a decision-maker -- it surfaces information and perspectives, the user decides
