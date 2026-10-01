"""
Standard Model Context Protocol (MCP) stdio Server for Game Data Analytics.
Complies with Anthropic/Cursor/Antigravity JSON-RPC 2.0 MCP specification.
"""
import sys
import json
import logging
from typing import Dict, Any
from .tools import TOOL_DEFINITIONS, dispatch_tool_call

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(asctime)s] [game-data-mcp] %(levelname)s: %(message)s"
)
logger = logging.getLogger("mcp_server")

def handle_rpc_request(request: Dict[str, Any]) -> Dict[str, Any] | None:
    method = request.get("method")
    req_id = request.get("id")
    params = request.get("params", {})

    logger.info(f"Handling method: {method} (id={req_id})")

    # Notifications do not return a response
    if req_id is None:
        if method == "notifications/initialized":
            logger.info("Client completed initialization handshake.")
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "game-data-analyst-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOL_DEFINITIONS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        logger.info(f"Invoking tool '{tool_name}' with args {arguments}")

        try:
            result = dispatch_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ],
                    "isError": not result.get("success", True)
                }
            }
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"success": False, "error": str(e)})
                        }
                    ],
                    "isError": True
                }
            }

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found."
            }
        }

def start_server():
    logger.info("Game Data Analyst MCP Server started over stdio.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_rpc_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError as err:
            logger.error(f"Failed to parse incoming JSON: {err}")
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    start_server()
