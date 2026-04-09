from __future__ import annotations

import os
import re
import asyncio
import sqlite3
from typing import Any, Optional, Annotated
from pydantic import Field
from dotenv import load_dotenv

from fastmcp import FastMCP

# ---------------------------------------------------------
# Config & storage
# ---------------------------------------------------------
load_dotenv()

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000")
DB_PATH = os.environ.get("BOOKMARKS_DB", "./bookmarks.db")

# Basic URL check (keep it lightweight; real apps should use robust validation)
_URL_RE = re.compile(r"^https?://[\w\-.:/%?#=&+]+$", re.IGNORECASE)

def _init_db_sync() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_sub TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

async def init_db() -> None:
    await asyncio.to_thread(_init_db_sync)

def _exec(sql: str, params: tuple = ()) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return lid

async def db_exec(sql: str, params: tuple = ()) -> int:
    return await asyncio.to_thread(_exec, sql, params)


def _query(sql: str, params: tuple = ()) -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

async def db_query(sql: str, params: tuple = ()) -> list[tuple]:
    return await asyncio.to_thread(_query, sql, params)

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
async def add_bookmark(
    url: Annotated[str, Field(description="Full URL starting with http(s)://")],
    title: Annotated[Optional[str], Field(description="Optional human title")] = None,
    tags: Annotated[Optional[list[str]], Field(description="Optional tags")] = None,
) -> dict[str, Any]:
    """Add a bookmark to your personal collection."""
    if not _URL_RE.match(url):
        raise ValueError("Invalid URL. Must start with http:// or https://")

    await init_db()
    norm_title = _normalize_title(title, url)
    tag_str = _tags_to_str(tags)

    lid = await db_exec(
        "INSERT INTO bookmarks (user_sub, url, title, tags) VALUES (?, ?, ?, ?)",
        ("global", url, norm_title, tag_str),
    )
    return {"id": lid, "saved": True, "url": url, "title": norm_title, "tags": (tags or [])}


@mcp.tool
async def list_bookmarks(
    limit: Annotated[int, Field(description="Max items", ge=1, le=100)] = 20
) -> dict[str, Any]:
    """List your most recent bookmarks."""
    await init_db()
    rows = await db_query(
        "SELECT id, url, title, tags, created_at FROM bookmarks ORDER BY id DESC LIMIT ?",
        (limit),
    )
    items = []
    for r in rows:
        _id, url, title, tags, created_at = r
        items.append({
            "id": _id,
            "url": url,
            "title": title or "",
            "tags": (tags or '').split(',') if tags else [],
            "created_at": created_at,
        })
    return {"items": items}


if __name__ == "__main__":
    asyncio.run(init_db())
    # be explicit so the provider can expose /.well-known/.../mcp
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        path="/mcp"
    )