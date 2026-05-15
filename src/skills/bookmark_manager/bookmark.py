import re
from typing import Any, Optional, Annotated
from urllib.parse import urlparse

from pydantic import Field
from fastmcp import FastMCP

import core.notion as notion_core
from core.notion import notion, init_db, _URL_RE


_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _normalize_title(title: Optional[str], url: str) -> str:
    title = (title or "").strip()
    if title:
        return title

    try:
        p = urlparse(url)
        base = p.netloc
        tail = (p.path or "/").rstrip("/")
        return base + (tail if tail else "/")
    except Exception:
        return url


def register_bookmark_tools(mcp: FastMCP):

# ---------------------------------------------------------
# add_bookmark tool
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
            "ID": {   
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
            parent={"data_source_id": notion_core.BOOKMARK_DATA_SOURCE_ID},
            properties=properties,
        )

        return {
            "id": page["id"],
            "saved": True,
            "url": url,
            "title": norm_title,
            "tags": tags or [],
        }
    
    # ---------------------------------------------------------
    # list_bookmarks tool
    # ---------------------------------------------------------
    @mcp.tool
    async def list_bookmarks(
        limit: Annotated[int, Field(description="Max items", ge=1, le=100)] = 20
    ) -> dict[str, Any]:

        await init_db()

        response = notion.data_sources.query(
            data_source_id=notion_core.BOOKMARK_DATA_SOURCE_ID,
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
    # delete_bookmark tool 
    # ---------------------------------------------------------
    @mcp.tool()
    async def delete_bookmark(
        bookmark_id: Annotated[str, Field(description="ID of the bookmark to delete")]
    ) -> dict[str, Any]:

        await init_db()

        # Notion doesn't have a hard delete, so we "archive" the page
        notion.pages.update(
            page_id=bookmark_id,
            archived=True
        )

        return {
            "id": bookmark_id,
            "deleted": True,
        }