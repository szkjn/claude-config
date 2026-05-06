---
name: utils-notion
description: Read Notion pages via the API (by URL, or via branch→page link) and manage the PR ↔ Notion ticket link. Use this skill when the user runs /utils-notion, /utils-notion fetch, /utils-notion link, /utils-notion read, or /utils-notion update.
allowed-tools: Bash, Read
---

# utils-notion

Read any Notion page as Markdown, or manage the PR ↔ Notion ticket link for the current git branch. No MCP involved -- all API calls go through `notion_ctx.py` using a long-lived integration token. The script loads `.env` automatically via `python-dotenv`.

## Commands

| User invocation | Script command | Effect |
|---|---|---|
| `/utils-notion fetch <url-or-id>` | `fetch <url-or-id>` | Fetch any Notion page by URL or ID and print its content as Markdown. No DB config needed. |
| `/utils-notion link <url>` | `link <url>` | Write current branch name to the `Branch` property of the given Notion page (one-time per feature) |
| `/utils-notion link --title "<title>"` | `link --title "<title>"` | Same as above but find the page by title search across configured databases |
| `/utils-notion` or `/utils-notion read` | `read` | Fetch the page linked to the current branch and inject its content as Markdown context |
| `/utils-notion update` | `update --field <name> --value <value>` | Update an arbitrary property on the linked page |
| `/utils-notion append` | `append --file <path>` | Append a Markdown file (or stdin with `--file -`) as blocks to the linked page |

## How to run

```bash
uv run .claude/skills/utils-notion/notion_ctx.py <command>
```

## Workflow per sub-command

### `/utils-notion fetch <url-or-id>`

Run:
```bash
uv run .claude/skills/utils-notion/notion_ctx.py fetch <url-or-id>
```

Print the script output verbatim. Accepts a full Notion URL or a bare page ID (with or without dashes). Only requires `NOTION_API_KEY` -- does not need the DB IDs.

### `/utils-notion link <url>` or `--title "..."`

Run:
```bash
uv run .claude/skills/utils-notion/notion_ctx.py link <url>
# or
uv run .claude/skills/utils-notion/notion_ctx.py link --title "<title>"
```

Report success or error to the user.

### `/utils-notion` or `/utils-notion read`

Run:
```bash
uv run .claude/skills/utils-notion/notion_ctx.py read
```

Print the script output verbatim. The output is compact Markdown (~200-500 tokens) with the page title, status, assignee, branch, and body.

If the script exits with "No Notion page linked", tell the user to run `/utils-notion link <url>` first.

### `/utils-notion update`

Ask the user which field and value to update (if not already specified in the invocation).
Then run:
```bash
uv run .claude/skills/utils-notion/notion_ctx.py update --field "<field>" --value "<value>"
```

Supported property types: `title`, `rich_text`, `select`, `status`, `multi_select`, `checkbox`, `number`, `url`, `email`, `phone_number`, `people`.

For `people`-type properties, `--value` accepts a comma-separated list of user IDs, emails (exact), or name substrings — the script resolves them via the Notion users API.

Report success or error. Status changes can also be done manually in Notion.

### `/utils-notion append`

Run:
```bash
uv run .claude/skills/utils-notion/notion_ctx.py append --file <path>
# or pipe from stdin
echo "# Title\n\n- bullet" | uv run .claude/skills/utils-notion/notion_ctx.py append --file -
```

Appends parsed Markdown as Notion blocks to the page linked to the current branch. Supports block types H1/H2/H3, bullets (`-`/`*`), numbered lists, quotes (`>`), code fences, and paragraphs, plus inline `**bold**`, `*italic*`, `_italic_`, and `` `code` `` rendered as Notion rich-text annotations. Chunks automatically at the 100-block API limit.

## Required env vars

| Variable | Purpose | Required for |
|---|---|---|
| `NOTION_API_KEY` | Notion integration token | all commands |
| `NOTION_FEATURES_DB_ID` | ID of the Features database in Notion | `read`, `link`, `update` |
| `NOTION_ISSUES_DB_ID` | ID of the Issues/Bugs database in Notion | `read`, `link`, `update` |

At least one of `NOTION_FEATURES_DB_ID` / `NOTION_ISSUES_DB_ID` must be set for the branch-linked commands. `read`, `link`, and `update` search all configured databases and return the first match. `fetch` only needs `NOTION_API_KEY`.

## One-time Notion setup

1. Add a **`Branch`** property of type **Text** to both the Features and Issues/Bugs databases in Notion
2. Share each database with the Notion integration that owns `NOTION_API_KEY`

## Notes

- Output is compact Markdown (headings, lists, code blocks, quotes, callouts, recursive toggles).
- Non-textual blocks (table, bookmark, child_page) are signalled with a `[...]` tag.
- The Notion API is paginated; the script handles pagination automatically (page_size=100).
