# skills/workflow-runtime/mcp/registry.py

MCP_TOOLS = [
    {
        "name": "aiwf_submit_workflow",
        "description": "Submits a new engineering task into AIWF Workflow Runtime",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string", 
                    "description": "The engineering task description (e.g. 'Add Google OAuth login')"
                },
                "session_id": {
                    "type": "string", 
                    "description": "Optional session ID for the trajectory"
                }
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
                "workflow_id": {
                    "type": "string", 
                    "description": "Workflow ID (e.g. FEAT-313)"
                }
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
                "workflow_id": {
                    "type": "string", 
                    "description": "Workflow ID"
                },
                "last_event_id": {
                    "type": "integer", 
                    "description": "Starting index for events log (default: 0)"
                }
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
                "workflow_id": {
                    "type": "string", 
                    "description": "Workflow ID"
                }
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
                "workflow_id": {
                    "type": "string", 
                    "description": "Workflow ID"
                }
            },
            "required": ["workflow_id"]
        }
    }
]

def get_mcp_tools() -> list:
    return MCP_TOOLS
