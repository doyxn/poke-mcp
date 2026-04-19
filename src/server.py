import os
import logging
import re
import asyncio
from pprint import pprint
from dotenv import load_dotenv

from notion_client import Client
from fastmcp import FastMCP
from pydantic import Field
from typing import Any, Optional, Annotated

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
load_dotenv()

notion = Client(
    auth=os.environ.get("NOTION_INTEGRATION_SECRET"),
    log_level=logging.DEBUG,
)

# Globals for cached IDs
BOOKMARK_DATA_SOURCE_ID: Optional[str] = None
KANBAN_DATA_SOURCE_ID: Optional[str] = None

# Simple URL validation
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)

# ---------------------------------------------------------
# MCP app
# ---------------------------------------------------------
DEFAULT_USER = "global"

mcp = FastMCP(
    name="Bookmark Manager MCP",
    instructions=(
        "Simple bookmark manager. "
        "Use add_bookmark(url, title?, tags?) to save, "
        "and list_bookmarks(limit?) to view."
    ),
)

# ---------------------------------------------------------
# Init (Notion “DB” setup)
# ---------------------------------------------------------
async def init_db():
    global BOOKMARK_DATA_SOURCE_ID, KANBAN_DATA_SOURCE_ID

    if BOOKMARK_DATA_SOURCE_ID and KANBAN_DATA_SOURCE_ID:
        return

    bookmark_db = notion.databases.retrieve(
        database_id=os.environ.get("NOTION_BOOKMARKS_DATABASE_ID")
    )

    kanban_db = notion.databases.retrieve(
        database_id=os.environ.get("NOTION_KANBAN_DATABASE_ID")
    )

    BOOKMARK_DATA_SOURCE_ID = bookmark_db["data_sources"][0]["id"]
    KANBAN_DATA_SOURCE_ID = kanban_db["data_sources"][0]["id"]

# ---------------------------------------------------------
# MCP tools
# ---------------------------------------------------------
@mcp.tool
async def add_bookmark(
    url: Annotated[str, Field(description="Full URL starting with http(s)://")],
    title: Annotated[Optional[str], Field(description="Optional human title")] = None,
    tags: Annotated[Optional[list[str]], Field(description="Optional tags")] = None,
) -> dict[str, Any]:

    await init_db()

    if not _URL_RE.match(url):
        raise ValueError("Invalid URL. Must start with http:// or https://")

    norm_title = _normalize_title(title, url)

    properties = {
        "ID": {   # 👈 THIS is your title field
            "title": [
                {"text": {"content": norm_title}}
            ]
        },
        "url": {
            "url": url
        },
        "tags": {
            "rich_text": [
                {"text": {"content": ",".join(tags)}} if tags else {"text": {"content": ""}}
            ]
        }
    }

    page = notion.pages.create(
        parent={"data_source_id": BOOKMARK_DATA_SOURCE_ID},
        properties=properties,
    )

    return {
        "id": page["id"],
        "saved": True,
        "url": url,
        "title": norm_title,
        "tags": tags or [],
    }


@mcp.tool
async def list_bookmarks(
    limit: Annotated[int, Field(description="Max items", ge=1, le=100)] = 20
) -> dict[str, Any]:

    await init_db()

    response = notion.data_sources.query(
        data_source_id=BOOKMARK_DATA_SOURCE_ID,
        page_size=limit,
        sorts=[{"timestamp": "created_time", "direction": "descending"}],
    )

    items = []

    for page in response["results"]:
        props = page["properties"]

        title = ""
        if props.get("ID", {}).get("title"):
            title = props["ID"]["title"][0]["plain_text"]

        url = props.get("url", {}).get("url", "")

        tags = ""
        if props.get("tags", {}).get("rich_text"):
            tags = props["tags"]["rich_text"][0]["plain_text"]

        items.append({
            "id": page["id"],
            "url": url,
            "title": title,
            "tags": tags,
            "created_at": page["created_time"],
        })

    return {"items": items}


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _normalize_title(title: Optional[str], url: str) -> str:
    title = (title or "").strip()
    if title:
        return title
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        base = p.netloc
        tail = (p.path or "/").rstrip("/")
        return base + (tail if tail else "/")
    except Exception:
        return url


# ---------------------------------------------------------
# Run server
# ---------------------------------------------------------
if __name__ == "__main__":
    # Optional pre-init (can remove if you prefer lazy init)
    asyncio.run(init_db())

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        path="/mcp"
    )