---
name: sync-notion
description: Link the current branch to a Notion page, fetch its context, or update its properties. Use this skill when the user runs /sync-notion, /sync-notion link, /sync-notion read, or /sync-notion update.
---

# sync-notion

Manage the PR ↔ Notion ticket link for the current branch. No MCP involved -- all API calls go through `notion_ctx.py` using a long-lived integration token.

## Commands

| User invocation | Script command | Effect |
|---|---|---|
| `/sync-notion link <url>` | `link <url>` | Write current branch name to the `Branch` property of the given Notion page (one-time per feature) |
| `/sync-notion` or `/sync-notion read` | `read` | Fetch the linked page and inject its content as Markdown context |
| `/sync-notion update` | `update --field <name> --value <value>` | Update an arbitrary property on the linked page |

## How to run

Always source `.env` before running the script:

```bash
set -a && source .env && set +a && uv run python .claude/skills/sync-notion/notion_ctx.py <command>
```

## Workflow per sub-command

### `/sync-notion link <url>`

Run:
```bash
set -a && source .env && set +a && uv run python .claude/skills/sync-notion/notion_ctx.py link <url>
```

Report success or error to the user.

### `/sync-notion` or `/sync-notion read`

Run:
```bash
set -a && source .env && set +a && uv run python .claude/skills/sync-notion/notion_ctx.py read
```

Print the script output verbatim. The output is compact Markdown (~200-500 tokens) with the page title, status, assignee, branch, and body.

If the script exits with "No Notion page linked", tell the user to run `/sync-notion link <url>` first.

### `/sync-notion update`

Ask the user which field and value to update (if not already specified in the invocation).
Then run:
```bash
set -a && source .env && set +a && uv run python .claude/skills/sync-notion/notion_ctx.py update --field "<field>" --value "<value>"
```

Report success or error. Status changes can also be done manually in Notion.

## Required env vars

| Variable | Purpose |
|---|---|
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_FEATURES_DB_ID` | ID of the Features database in Notion |
| `NOTION_ISSUES_DB_ID` | ID of the Issues/Bugs database in Notion |

At least one of `NOTION_FEATURES_DB_ID` / `NOTION_ISSUES_DB_ID` must be set. `read` and `update` search both databases and return the first match.

## One-time Notion setup

1. Add a **`Branch`** property of type **Text** to both the Features and Issues/Bugs databases in Notion
