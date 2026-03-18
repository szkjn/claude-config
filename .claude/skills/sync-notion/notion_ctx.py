#!/usr/bin/env python
"""Notion context script -- links git branches to Notion pages and fetches page content."""

import argparse
import os
import re
import subprocess
import sys

import httpx


def get_api_key():
    key = os.environ.get("NOTION_API_KEY")
    if not key:
        print("Error: NOTION_API_KEY must be set", file=sys.stderr)
        sys.exit(1)
    return key


def get_db_ids():
    """Return all configured database IDs. At least one must be set."""
    db_ids = []
    for var in ("NOTION_FEATURES_DB_ID", "NOTION_ISSUES_DB_ID"):
        val = os.environ.get(var, "").strip()
        if val:
            db_ids.append(val)
    if not db_ids:
        print("Error: at least one of NOTION_FEATURES_DB_ID or NOTION_ISSUES_DB_ID must be set", file=sys.stderr)
        sys.exit(1)
    return db_ids


def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: not inside a git repository", file=sys.stderr)
        sys.exit(1)
    branch = result.stdout.strip()
    if not branch:
        print("Error: could not determine current branch (detached HEAD?)", file=sys.stderr)
        sys.exit(1)
    return branch


def notion_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def extract_page_id(page_url_or_id):
    """Extract a Notion page ID from a URL or bare ID string."""
    # Strip query string / fragment
    url = page_url_or_id.split("?")[0].split("#")[0].rstrip("/")
    # Last path segment may be "Page-Title-<id>" or just "<id>"
    segment = url.split("/")[-1]
    # UUIDs with or without dashes (32 hex chars)
    match = re.search(r"([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})", segment, re.I)
    if match:
        raw = match.group(1).replace("-", "")
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    # Fallback: treat whole segment as ID (32 hex chars without dashes)
    if re.fullmatch(r"[0-9a-f]{32}", segment, re.I):
        return f"{segment[:8]}-{segment[8:12]}-{segment[12:16]}-{segment[16:20]}-{segment[20:]}"
    print(f"Error: could not parse page ID from: {page_url_or_id}", file=sys.stderr)
    sys.exit(1)


def query_page_by_branch(api_key, db_ids, branch):
    """Search all configured databases for a page whose Branch property equals branch."""
    for db_id in db_ids:
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        payload = {
            "filter": {
                "property": "Branch",
                "rich_text": {"equals": branch},
            }
        }
        resp = httpx.post(url, headers=notion_headers(api_key), json=payload)
        if resp.status_code != 200:
            continue
        results = resp.json().get("results", [])
        if results:
            return results
    return []


def get_page(api_key, page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = httpx.get(url, headers=notion_headers(api_key))
    if resp.status_code != 200:
        print(f"Error fetching page: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def get_blocks(api_key, block_id):
    """Fetch all child blocks (handles pagination)."""
    blocks = []
    cursor = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children"
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = httpx.get(url, headers=notion_headers(api_key), params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks


def extract_rich_text(rich_text_list):
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def blocks_to_markdown(blocks, depth=0):
    lines = []
    indent = "  " * depth
    for block in blocks:
        btype = block.get("type")
        content = block.get(btype, {})

        if btype == "paragraph":
            text = extract_rich_text(content.get("rich_text", []))
            lines.append(f"{indent}{text}" if text else "")
        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = int(btype[-1])
            text = extract_rich_text(content.get("rich_text", []))
            lines.append(f"{'#' * level} {text}")
        elif btype == "bulleted_list_item":
            text = extract_rich_text(content.get("rich_text", []))
            lines.append(f"{indent}- {text}")
        elif btype == "numbered_list_item":
            text = extract_rich_text(content.get("rich_text", []))
            lines.append(f"{indent}1. {text}")
        elif btype == "to_do":
            text = extract_rich_text(content.get("rich_text", []))
            checked = content.get("checked", False)
            mark = "x" if checked else " "
            lines.append(f"{indent}- [{mark}] {text}")
        elif btype == "toggle":
            text = extract_rich_text(content.get("rich_text", []))
            lines.append(f"{indent}- {text}")
        elif btype == "code":
            text = extract_rich_text(content.get("rich_text", []))
            lang = content.get("language", "")
            lines.append(f"```{lang}\n{text}\n```")
        elif btype == "quote":
            text = extract_rich_text(content.get("rich_text", []))
            lines.append(f"> {text}")
        elif btype == "divider":
            lines.append("---")
        elif btype == "callout":
            text = extract_rich_text(content.get("rich_text", []))
            lines.append(f"> {text}")
        # Ignore unsupported block types silently

        # Recurse into children if present
        if block.get("has_children"):
            # Children not fetched here; caller handles recursion if needed
            pass

    return "\n".join(lines)


def page_to_markdown(api_key, page):
    """Render a Notion page as compact Markdown."""
    props = page.get("properties", {})

    # Title
    title = ""
    for key in ("Name", "Titre", "Title", "title"):
        if key in props:
            title_prop = props[key]
            ptype = title_prop.get("type")
            if ptype == "title":
                title = extract_rich_text(title_prop.get("title", []))
                break

    # Status
    status = ""
    for key in ("Status", "Statut"):
        if key in props:
            status_prop = props[key]
            ptype = status_prop.get("type")
            if ptype == "status":
                status = status_prop.get("status", {}).get("name", "")
            elif ptype == "select":
                status = (status_prop.get("select") or {}).get("name", "")
            break

    # Assignee
    assignee = ""
    for key in ("Assignee", "Assigné", "Assigned to"):
        if key in props:
            people = props[key].get("people", [])
            assignee = ", ".join(p.get("name", "") for p in people)
            break

    # Branch
    branch = ""
    if "Branch" in props:
        branch = extract_rich_text(props["Branch"].get("rich_text", []))

    # Fetch body blocks
    page_id = page["id"]
    blocks = get_blocks(api_key, page_id)
    body = blocks_to_markdown(blocks)

    lines = [f"# {title}"]
    if status:
        lines.append(f"**Status:** {status}")
    if assignee:
        lines.append(f"**Assignee:** {assignee}")
    if branch:
        lines.append(f"**Branch:** {branch}")
    lines.append("")
    if body.strip():
        lines.append(body)

    return "\n".join(lines)


def cmd_read(args):
    api_key = get_api_key()
    db_ids = get_db_ids()
    branch = get_current_branch()

    results = query_page_by_branch(api_key, db_ids, branch)
    if not results:
        print(f"No Notion page linked to branch '{branch}'.")
        print("Run: uv run .claude/skills/notion/notion_ctx.py link <page_url>")
        sys.exit(1)

    page = results[0]
    print(page_to_markdown(api_key, page))


def cmd_link(args):
    api_key = get_api_key()
    branch = get_current_branch()
    page_id = extract_page_id(args.page_url)

    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Branch": {
                "rich_text": [{"type": "text", "text": {"content": branch}}]
            }
        }
    }
    resp = httpx.patch(url, headers=notion_headers(api_key), json=payload)
    if resp.status_code != 200:
        print(f"Error updating page: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    print(f"Linked branch '{branch}' to Notion page {page_id}")


def cmd_update(args):
    api_key = get_api_key()
    db_ids = get_db_ids()
    branch = get_current_branch()

    results = query_page_by_branch(api_key, db_ids, branch)
    if not results:
        print(f"No Notion page linked to branch '{branch}'.")
        sys.exit(1)

    page_id = results[0]["id"]
    field = args.field
    value = args.value

    # Determine payload based on common field types
    # Try to detect the property type from the page
    page = get_page(api_key, page_id)
    props = page.get("properties", {})

    if field not in props:
        print(f"Error: property '{field}' not found on page. Available: {', '.join(props.keys())}", file=sys.stderr)
        sys.exit(1)

    prop = props[field]
    ptype = prop.get("type")

    if ptype == "rich_text":
        payload_prop = {"rich_text": [{"type": "text", "text": {"content": value}}]}
    elif ptype == "title":
        payload_prop = {"title": [{"type": "text", "text": {"content": value}}]}
    elif ptype == "select":
        payload_prop = {"select": {"name": value}}
    elif ptype == "status":
        payload_prop = {"status": {"name": value}}
    elif ptype == "multi_select":
        payload_prop = {"multi_select": [{"name": v.strip()} for v in value.split(",")]}
    elif ptype == "checkbox":
        payload_prop = {"checkbox": value.lower() in ("true", "1", "yes")}
    elif ptype == "number":
        payload_prop = {"number": float(value)}
    elif ptype == "url":
        payload_prop = {"url": value}
    elif ptype == "email":
        payload_prop = {"email": value}
    elif ptype == "phone_number":
        payload_prop = {"phone_number": value}
    else:
        print(f"Error: unsupported property type '{ptype}' for field '{field}'", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = httpx.patch(url, headers=notion_headers(api_key), json={"properties": {field: payload_prop}})
    if resp.status_code != 200:
        print(f"Error updating page: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    print(f"Updated '{field}' to '{value}' on Notion page {page_id}")


def main():
    parser = argparse.ArgumentParser(description="Notion context for PR workflows")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("read", help="Print linked Notion page as Markdown").set_defaults(func=cmd_read)

    p_link = subparsers.add_parser("link", help="Link current branch to a Notion page")
    p_link.add_argument("page_url", help="Notion page URL or ID")
    p_link.set_defaults(func=cmd_link)

    p_update = subparsers.add_parser("update", help="Update a property on the linked Notion page")
    p_update.add_argument("--field", required=True, help="Property name to update")
    p_update.add_argument("--value", required=True, help="New value")
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
