from __future__ import annotations

import os
import re
import asyncio
import sqlite3
from typing import Any, Optional, Annotated
from pydantic import Field
from dotenv import load_dotenv

from fastmcp import FastMCP
from notion_client import AsyncClient
# ---------------------------------------------------------
# Config & storage
# ---------------------------------------------------------
load_dotenv()

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000")
notion  = AsyncClient(auth=os.environ.get("NOTION_INTEGRATION_TOKEN"))
NOTION_DB_ID = os.environ.get("NOTION_DATABASE_ID")


# Basic URL check (keep it lightweight; real apps should use robust validation)
_URL_RE = re.compile(r"^https?://[\w\-.:/%?#=&+]+$", re.IGNORECASE)



# ---------------------------------------------------------
# MCP app
# ---------------------------------------------------------
DEFAULT_USER = "global" #
mcp = FastMCP(
    name="Bookmark Manager MCP",
    instructions=(
        "Simple bookmark manager. "
        "Use add_bookmark(DEFAULT_USER, url, title?, tags?) to save, and list_bookmarks(limit?) to view. "
        "All data is scoped to the user's token claims."
    ),
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _tags_to_str(tags: Optional[list[str]]) -> str:
    return ",".join(t.strip() for t in (tags or []) if t.strip())


def _normalize_title(title: Optional[str], url: str) -> str:
    title = (title or "").strip()
    if title:
        return title
    # fallback: hostname path snippet
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        base = p.netloc
        tail = (p.path or "/").rstrip("/")
        return base + (tail if tail else "/")
    except Exception:
        return url


# ---------------------------------------------------------
# Tools
# ---------------------------------------------------------
@mcp.tool
async def add_bookmark(url: str, title: str = None) -> dict:
    """Saves a bookmark directly to your Notion Database."""
    new_page = await notion.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties={
            "Name": {"title": [{"text": {"content": title or url}}]},
            "URL": {"url": url},
            "Status": {"select": {"name": "Saved"}}
        }
    )
    return {"status": "success", "id": new_page["id"]}


if __name__ == "__main__":
    # be explicit so the provider can expose /.well-known/.../mcp
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        path="/mcp"
    )