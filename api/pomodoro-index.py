# api/index.py

import json
from handle_mcp import handle_mcp_request  # adjust import as needed

def handler(request):
    try:
        method = request.method

        # --- CORS headers ---
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        # --- Handle preflight ---
        if method == "OPTIONS":
            return ( "", 200, headers )

        # --- GET (health check) ---
        if method == "GET":
            response = {
                "name": "PokeMCP",
                "version": "1.0.0",
                "status": "running",
                "tools": 5,
                "resources": 1
            }
            return (json.dumps(response), 200, headers)

        # --- POST (MCP requests) ---
        if method == "POST":
            try:
                body = request.get_data(as_text=True)
                if body:
                    request_data = json.loads(body)
                    response = handle_mcp_request(request_data)
                else:
                    response = {"error": "No data received"}

                return (json.dumps(response), 200, headers)

            except Exception as e:
                return (json.dumps({"error": str(e)}), 500, headers)

        # --- Unsupported method ---
        return (json.dumps({"error": f"Method {method} not allowed"}), 405, headers)

    except Exception as e:
        return (
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            500,
            {"Content-Type": "application/json"}
        )