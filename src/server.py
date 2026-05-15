import os
import asyncio
from fastmcp import FastMCP

from core.notion import init_db
from skills.bookmark_manager.bookmark import register_bookmark_tools

mcp = FastMCP(
    name="Bookmark Manager MCP",
    instructions=(
        "Simple bookmark manager. "
        "Use add_bookmark(url, title?, tags?) to save, "
        "and list_bookmarks(limit?) to view."
    ),
)

# register all tool modules
register_bookmark_tools(mcp)

if __name__ == "__main__":
    asyncio.run(init_db())

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        path="/mcp"
    )