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

