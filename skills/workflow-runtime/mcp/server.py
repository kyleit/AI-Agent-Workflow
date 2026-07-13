import os
import sys
import json
import traceback

# Add script and adapter paths to sys.path
adapters_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "adapters"))
if adapters_dir not in sys.path:
    sys.path.insert(0, adapters_dir)
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from antigravity_gateway import AntigravityGatewayAdapter

def handle_tools_list() -> dict:
    return {
        "tools": [
            {
                "name": "aiwf_submit_workflow",
                "description": "Submits a new engineering task into AIWF Workflow Runtime",
                "inputSchema": {
                  "type": "object",
                  "properties": {
                    "task": {"type": "string", "description": "The engineering task description"},
                    "session_id": {"type": "string", "description": "Optional session ID"}
                  },
                  "required": ["task"]
                }
            },
            {
                "name": "aiwf_workflow_status",
                "description": "Checks status and phase of a given workflow ID",
                "inputSchema": {
                  "type": "object",
                  "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID (e.g. FEAT-313)"}
                  },
                  "required": ["workflow_id"]
                }
            },
            {
                "name": "aiwf_workflow_follow",
                "description": "Tails newly appended events since last_event_id for a workflow",
                "inputSchema": {
                  "type": "object",
                  "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"},
                    "last_event_id": {"type": "integer", "description": "Starting index for events log"}
                  },
                  "required": ["workflow_id"]
                }
            },
            {
                "name": "aiwf_workflow_agents",
                "description": "Returns active agents allocated to a workflow",
                "inputSchema": {
                  "type": "object",
                  "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"}
                  },
                  "required": ["workflow_id"]
                }
            },
            {
                "name": "aiwf_workflow_timeline",
                "description": "Aggregates events timeline for a workflow",
                "inputSchema": {
                  "type": "object",
                  "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"}
                  },
                  "required": ["workflow_id"]
                }
            }
        ]
    }

def handle_tools_call(name: str, arguments: dict) -> dict:
    adapter = AntigravityGatewayAdapter()
    
    if name == "aiwf_submit_workflow":
        task = arguments.get("task")
        session_id = arguments.get("session_id")
        res = adapter.submit_workflow(task, session_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, indent=2)
                }
            ]
        }
    elif name == "aiwf_workflow_status":
        wf_id = arguments.get("workflow_id")
        res = adapter.get_workflow_status(wf_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, indent=2)
                }
            ]
        }
    elif name == "aiwf_workflow_follow":
        wf_id = arguments.get("workflow_id")
        last_id = arguments.get("last_event_id", 0)
        res = adapter.follow_workflow(wf_id, last_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, indent=2)
                }
            ]
        }
    elif name == "aiwf_workflow_agents":
        wf_id = arguments.get("workflow_id")
        res = adapter.get_workflow_agents(wf_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, indent=2)
                }
            ]
        }
    elif name == "aiwf_workflow_timeline":
        wf_id = arguments.get("workflow_id")
        res = adapter.get_workflow_timeline(wf_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, indent=2)
                }
            ]
        }
    else:
        raise ValueError(f"Tool {name} not found")

def main():
    # Standard MCP JSON-RPC Server Loop
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")
            
            # Simple fallback for tools list or tool call
            if method == "tools/list" or method == "initialize":
                res = handle_tools_list()
                response = {
                    "jsonrpc": "2.0",
                    "result": res,
                    "id": req_id
                }
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = handle_tools_call(tool_name, tool_args)
                response = {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": req_id
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method {method} not found"
                    },
                    "id": req_id
                }
                
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            err_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e),
                    "data": traceback.format_exc()
                },
                "id": None
            }
            print(json.dumps(err_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
