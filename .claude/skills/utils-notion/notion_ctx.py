#!/usr/bin/env python
"""Notion context script — fetch Notion pages by URL, or by git-branch link for PR workflows."""

import argparse
import os
import re
import subprocess
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


def get_api_key():
    key = os.environ.get("NOTION_API_KEY")
    if not key:
        print("Error: NOTION_API_KEY must be set (check .env)", file=sys.stderr)
        sys.exit(1)
    return key


def get_db_ids():
    """Return all configured database IDs. At least one must be set (for link/read by branch)."""
    db_ids = []
    for var in ("NOTION_FEATURES_DB_ID", "NOTION_ISSUES_DB_ID"):
        val = os.environ.get(var, "").strip()
        if val:
            db_ids.append(val)
    if not db_ids:
        print(
            "Error: at least one of NOTION_FEATURES_DB_ID or NOTION_ISSUES_DB_ID must be set",
            file=sys.stderr,
        )
        sys.exit(1)
    return db_ids


def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Error: not inside a git repository", file=sys.stderr)
        sys.exit(1)
    branch = result.stdout.strip()
    if not branch:
        print("Error: could not determine current branch (detached HEAD?)", file=sys.stderr)
        sys.exit(1)
    return branch


def get_branch_ref():
    """Return '<repo>:<branch>' for use in the Notion Branch field."""
    branch = get_current_branch()
    toplevel = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    repo = os.path.basename(toplevel.stdout.strip()) if toplevel.returncode == 0 else ""
    return f"{repo}:{branch}" if repo else branch


def notion_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def extract_page_id(page_url_or_id):
    """Extract a Notion page ID from a URL or bare ID string."""
    url = page_url_or_id.split("?")[0].split("#")[0].rstrip("/")
    segment = url.split("/")[-1]
    match = re.search(
        r"([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})",
        segment,
        re.I,
    )
    if match:
        raw = match.group(1).replace("-", "")
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    if re.fullmatch(r"[0-9a-f]{32}", segment, re.I):
        return f"{segment[:8]}-{segment[8:12]}-{segment[12:16]}-{segment[16:20]}-{segment[20:]}"
    print(f"Error: could not parse page ID from: {page_url_or_id}", file=sys.stderr)
    sys.exit(1)


def query_page_by_branch(api_key, db_ids, branch):
    """Search all configured databases for a page whose Branch property equals branch."""
    for db_id in db_ids:
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        payload = {
            "filter": {"property": "Branch", "rich_text": {"equals": branch}}
        }
        resp = requests.post(url, headers=notion_headers(api_key), json=payload)
        if resp.status_code != 200:
            continue
        results = resp.json().get("results", [])
        if results:
            return results
    return []


def query_page_by_title(api_key, db_ids, title):
    """Search all configured databases for pages whose title contains the given string."""
    results = []
    for db_id in db_ids:
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        payload = {
            "filter": {
                "or": [
                    {"property": "Name", "title": {"contains": title}},
                    {"property": "Titre", "title": {"contains": title}},
                    {"property": "Title", "title": {"contains": title}},
                ]
            }
        }
        resp = requests.post(url, headers=notion_headers(api_key), json=payload)
        if resp.status_code == 200:
            results.extend(resp.json().get("results", []))
    return results


def get_page(api_key, page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = requests.get(url, headers=notion_headers(api_key))
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
        resp = requests.get(url, headers=notion_headers(api_key), params=params)
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


def blocks_to_markdown(api_key, blocks, depth=0, recurse=True):
    lines = []
    indent = "  " * depth
    for block in blocks:
        btype = block.get("type")
        content = block.get(btype, {})
        text = extract_rich_text(content.get("rich_text", []))

        if btype == "paragraph":
            lines.append(f"{indent}{text}" if text else "")
        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = int(btype[-1])
            lines.append(f"{'#' * level} {text}")
        elif btype == "bulleted_list_item":
            lines.append(f"{indent}- {text}")
        elif btype == "numbered_list_item":
            lines.append(f"{indent}1. {text}")
        elif btype == "to_do":
            mark = "x" if content.get("checked", False) else " "
            lines.append(f"{indent}- [{mark}] {text}")
        elif btype == "toggle":
            lines.append(f"{indent}- {text}")
        elif btype == "code":
            lang = content.get("language", "")
            lines.append(f"```{lang}\n{text}\n```")
        elif btype == "quote":
            lines.append(f"> {text}")
        elif btype == "divider":
            lines.append("---")
        elif btype == "callout":
            lines.append(f"> {text}")
        elif btype == "child_page":
            lines.append(f"{indent}[child page] {content.get('title', '')}")
        elif btype == "bookmark":
            lines.append(f"{indent}[bookmark] {content.get('url', '')}")
        elif btype == "table":
            lines.append(f"{indent}[table]")

        if recurse and block.get("has_children") and btype != "child_page":
            sub = get_blocks(api_key, block["id"])
            sub_md = blocks_to_markdown(api_key, sub, depth + 1, recurse=True)
            if sub_md:
                lines.append(sub_md)

    return "\n".join(lines)


def page_to_markdown(api_key, page):
    """Render a Notion page as compact Markdown."""
    props = page.get("properties", {})

    title = ""
    for key in ("Name", "Titre", "Title", "title"):
        if key in props:
            title_prop = props[key]
            if title_prop.get("type") == "title":
                title = extract_rich_text(title_prop.get("title", []))
                break

    status = ""
    for key in ("Status", "Statut"):
        if key in props:
            p = props[key]
            if p.get("type") == "status":
                status = (p.get("status") or {}).get("name", "")
            elif p.get("type") == "select":
                status = (p.get("select") or {}).get("name", "")
            break

    assignee = ""
    for key in ("Assignee", "Assigné", "Assigned to"):
        if key in props:
            people = props[key].get("people", [])
            assignee = ", ".join(p.get("name", "") for p in people)
            break

    branch = ""
    if "Branch" in props:
        branch = extract_rich_text(props["Branch"].get("rich_text", []))

    blocks = get_blocks(api_key, page["id"])
    body = blocks_to_markdown(api_key, blocks)

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


def cmd_fetch(args):
    """Fetch any Notion page by URL or ID and print as Markdown."""
    api_key = get_api_key()
    page_id = extract_page_id(args.page_url)
    page = get_page(api_key, page_id)
    print(page_to_markdown(api_key, page))


def cmd_read(args):
    """Fetch the Notion page linked to the current git branch."""
    api_key = get_api_key()
    db_ids = get_db_ids()
    branch = get_branch_ref()
    results = query_page_by_branch(api_key, db_ids, branch)
    if not results:
        print(f"No Notion page linked to branch '{branch}'.")
        print("Run: uv run .claude/skills/utils-notion/notion_ctx.py link <page_url>")
        sys.exit(1)
    print(page_to_markdown(api_key, results[0]))


def cmd_link(args):
    """Link the current git branch to a Notion page via its Branch property."""
    api_key = get_api_key()
    branch_ref = get_branch_ref()

    if args.title:
        db_ids = get_db_ids()
        results = query_page_by_title(api_key, db_ids, args.title)
        if not results:
            print(f"Error: no page found with title containing '{args.title}'", file=sys.stderr)
            sys.exit(1)
        if len(results) > 1:
            titles = []
            for r in results:
                props = r.get("properties", {})
                t = ""
                for key in ("Name", "Titre", "Title", "title"):
                    if key in props and props[key].get("type") == "title":
                        t = extract_rich_text(props[key].get("title", []))
                        break
                titles.append(f"  - {t} ({r['id']})")
            print("Error: multiple pages matched. Refine:\n" + "\n".join(titles), file=sys.stderr)
            sys.exit(1)
        page_id = results[0]["id"]
    else:
        page_id = extract_page_id(args.page_url)

    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Branch": {"rich_text": [{"type": "text", "text": {"content": branch_ref}}]}
        }
    }
    resp = requests.patch(url, headers=notion_headers(api_key), json=payload)
    if resp.status_code != 200:
        print(f"Error updating page: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    print(f"Linked branch '{branch_ref}' to Notion page {page_id}")


def cmd_update(args):
    """Update a property on the Notion page linked to the current branch."""
    api_key = get_api_key()
    db_ids = get_db_ids()
    branch = get_branch_ref()
    results = query_page_by_branch(api_key, db_ids, branch)
    if not results:
        print(f"No Notion page linked to branch '{branch}'.")
        sys.exit(1)

    page_id = results[0]["id"]
    field, value = args.field, args.value
    page = get_page(api_key, page_id)
    props = page.get("properties", {})

    if field not in props:
        print(
            f"Error: property '{field}' not found. Available: {', '.join(props.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    ptype = props[field].get("type")
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
        print(f"Error: unsupported property type '{ptype}' for '{field}'", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = requests.patch(
        url, headers=notion_headers(api_key), json={"properties": {field: payload_prop}}
    )
    if resp.status_code != 200:
        print(f"Error updating page: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    print(f"Updated '{field}' to '{value}' on Notion page {page_id}")


def main():
    parser = argparse.ArgumentParser(description="Notion context — fetch/link/update pages")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_fetch = subparsers.add_parser("fetch", help="Fetch any Notion page by URL or ID")
    p_fetch.add_argument("page_url", help="Notion page URL or ID")
    p_fetch.set_defaults(func=cmd_fetch)

    subparsers.add_parser("read", help="Print Notion page linked to current branch").set_defaults(
        func=cmd_read
    )

    p_link = subparsers.add_parser("link", help="Link current branch to a Notion page")
    group = p_link.add_mutually_exclusive_group(required=True)
    group.add_argument("page_url", nargs="?", default=None, help="Notion page URL or ID")
    group.add_argument("--title", help="Search for a page by title substring")
    p_link.set_defaults(func=cmd_link)

    p_update = subparsers.add_parser("update", help="Update a property on the linked page")
    p_update.add_argument("--field", required=True)
    p_update.add_argument("--value", required=True)
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
