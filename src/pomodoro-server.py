# src/mcp_server.py
import json
from typing import Dict, Any, List

class MCPServer:
    """Vercel MCP server with Pomodoro and Kanban-style task management"""
    
    def __init__(self):
        self.tasks: Dict[str, List[str]] = {
            "backlog": [],
            "todo": [],
            "doing": [],
            "review": [],
            "done": []
        }

        self.tools = {
            "start_pomodoro_timer": {
                "name": "start_pomodoro_timer",
                "description": "Start a 25-minute Pomodoro timer for a task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Optional task to focus on"}
                    },
                    "required": []
                }
            },
            "add_task": {
                "name": "add_task",
                "description": "Add a task to the Kanban board with optional status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task description"},
                        "status": {"type": "string", "description": "Status column", "enum": ["backlog","todo","doing","review","done"]}
                    },
                    "required": ["task"]
                }
            },
            "delete_task": {
                "name": "delete_task",
                "description": "Delete a task from the Kanban board",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task description to delete"}
                    },
                    "required": ["task"]
                }
            },
            "list_tasks": {
                "name": "list_tasks",
                "description": "List all tasks grouped by status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "move_task": {
                "name": "move_task",
                "description": "Move a task from its current status to another status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task name to move"},
                        "status": {"type": "string", "description": "Target status", "enum": ["backlog","todo","doing","review","done"]}
                    },
                    "required": ["task", "status"]
                }
            }
        }
        
        self.resources = {
            "config://server": {
                "uri": "config://server",
                "name": "Server Configuration",
                "description": "Server configuration information",
                "mimeType": "application/json"
            }
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            method = request.get("method")
            
            if method == "initialize":
                return self._handle_initialize(request)
            elif method == "tools/list":
                return self._handle_tools_list(request)
            elif method == "tools/call":
                return self._handle_tools_call(request)
            elif method == "resources/list":
                return self._handle_resources_list(request)
            elif method == "resources/read":
                return self._handle_resources_read(request)
            else:
                return self._create_error_response(-32601, f"Method not found: {method}")
                
        except Exception as e:
            return self._create_error_response(-32603, f"Internal error: {str(e)}")
    
    def _handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "Vercel MCP Server", "version": "1.0.0"}
            }
        }
    
    def _handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0", 
            "id": request.get("id"),
            "result": {"tools": list(self.tools.values())}
        }
    
    def _handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        result = ""
        
        if tool_name == "start_pomodoro_timer":
            task = arguments.get("task", "No specific task")
            result = f"Pomodoro timer started for task: '{task}' (25 minutes)"
        
        elif tool_name == "add_task":
            task = arguments.get("task")
            status = arguments.get("status", "backlog")
            if status not in self.tasks:
                status = "backlog"
            self.tasks[status].append(task)
            result = f"Task added: '{task}' in status '{status}'"
        
        elif tool_name == "delete_task":
            task = arguments.get("task")
            found = False
            for status_list in self.tasks.values():
                if task in status_list:
                    status_list.remove(task)
                    found = True
                    break
            result = f"Task deleted: '{task}'" if found else f"Task not found: '{task}'"
        
        elif tool_name == "list_tasks":
            task_strings = []
            for status, tasks in self.tasks.items():
                task_strings.append(f"**{status.upper()}**")
                if tasks:
                    for t in tasks:
                        task_strings.append(f"- {t}")
                else:
                    task_strings.append("- (none)")
            result = "\n".join(task_strings)
        
        elif tool_name == "move_task":
            task = arguments.get("task")
            target_status = arguments.get("status")
            found = False
            for status_list in self.tasks.values():
                if task in status_list:
                    status_list.remove(task)
                    found = True
                    break
            if found:
                self.tasks[target_status].append(task)
                result = f"Task '{task}' moved to '{target_status}'"
            else:
                result = f"Task not found: '{task}'"
        
        else:
            return self._create_error_response(-32601, f"Tool not found: {tool_name}")
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "content": [{"type": "text", "text": result}]
            }
        }
    
    def _handle_resources_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"), 
            "result": {"resources": list(self.resources.values())}
        }
    
    def _handle_resources_read(self, request: Dict[str, Any]) -> Dict[str, Any]:
        params = request.get("params", {})
        uri = params.get("uri")
        
        if uri == "config://server":
            config = {
                "version": "1.0.0",
                "environment": "vercel", 
                "features": ["tools", "resources"]
            }
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(config, indent=2)
                    }]
                }
            }
        else:
            return self._create_error_response(-32601, f"Resource not found: {uri}")
    
    def _create_error_response(self, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message}
        }

# Create global instance
mcp = MCPServer()