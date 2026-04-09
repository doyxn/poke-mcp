# api/mcp.py
import asyncio
from fastmcp import FastMCP
from src.server import mcp  # import your MCP instance

async def handler(request):
    return await mcp.handle_request(request)

# Vercel automatically exposes this as /api/mcp