import subprocess
import json
import sys

def test_mcp():
    proc = subprocess.Popen(
        [sys.executable, "-m", "src.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    raw_init = proc.stdout.readline()
    if not raw_init.strip():
        raise AssertionError(f"Empty stdout from mcp_server (rc={proc.poll()}). STDERR:\n{proc.stderr.read()}")
    init_resp = json.loads(raw_init)
    print("Init Response Server Info:", init_resp["result"]["serverInfo"])

    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    proc.stdin.write(json.dumps(tools_req) + "\n")
    proc.stdin.flush()
    tools_resp = json.loads(proc.stdout.readline())
    tools = [t["name"] for t in tools_resp["result"]["tools"]]
    print("Tools Available:", tools)

    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "execute_safe_sql",
            "arguments": {
                "query": "SELECT title, global_sales FROM games WHERE publisher = 'Electronic Arts' ORDER BY global_sales DESC LIMIT 2"
            }
        }
    }
    proc.stdin.write(json.dumps(call_req) + "\n")
    proc.stdin.flush()
    call_resp = json.loads(proc.stdout.readline())
    content = json.loads(call_resp["result"]["content"][0]["text"])
    print("Tool Call Result (EA Top Titles):", content["rows"])

    proc.stdin.close()
    proc.terminate()
    print("ALL MCP PROTOCOL CHECKS PASSED!")

if __name__ == "__main__":
    test_mcp()
