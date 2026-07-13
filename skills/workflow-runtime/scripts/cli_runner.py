# cli_runner.py
import json
import argparse
import asyncio
import warnings
from typing import Any, Dict, List, Optional
from runtime_sdk import RuntimeSDKv3

class CLIRunner:
    def __init__(self, sdk: RuntimeSDKv3) -> None:
        self.sdk = sdk

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="AIWF CLI Runtime v3")
        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # 1. run command
        subparsers.add_parser("run", help="Run workflow task in-process")

        # 2. session sub-commands
        session_parser = subparsers.add_parser("session", help="Session Management")
        session_subs = session_parser.add_subparsers(dest="subcommand", help="Session actions")
        
        create_p = session_subs.add_parser("create", help="Create new session")
        create_p.add_argument("--permission-mode", default="sandbox")
        
        session_subs.add_parser("status", help="Get session status").add_argument("session_id")
        session_subs.add_parser("logs", help="Get session logs").add_argument("session_id")
        session_subs.add_parser("follow", help="Follow live session event stream").add_argument("session_id")
        session_subs.add_parser("resume", help="Resume interrupted session").add_argument("session_id")
        session_subs.add_parser("cancel", help="Cancel active session").add_argument("session_id")

        # 3. task sub-commands
        task_parser = subparsers.add_parser("task", help="Task Management")
        task_subs = task_parser.add_subparsers(dest="subcommand", help="Task actions")
        task_subs.add_parser("list", help="List tasks in session").add_argument("session_id")

        # 4. agents sub-commands
        agents_parser = subparsers.add_parser("agents", help="Agent Management")
        agents_subs = agents_parser.add_subparsers(dest="subcommand", help="Agent actions")
        agents_subs.add_parser("list", help="List active agents").add_argument("session_id")

        # 5. legacy orchestrator compatibility command
        orch_parser = subparsers.add_parser("orchestrator", help="Legacy orchestrator daemon control")
        orch_subs = orch_parser.add_subparsers(dest="subcommand", help="Legacy actions")
        orch_subs.add_parser("start", help="Start daemon")
        orch_subs.add_parser("stop", help="Stop daemon")
        orch_subs.add_parser("attach", help="Attach to daemon")
        orch_subs.add_parser("detach", help="Detach from daemon")

        return parser

    async def execute(self, args: List[str]) -> str:
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            return parser.format_help()

        # Handle run
        if parsed_args.command == "run":
            # Simulate running in-process session mode
            session = await self.sdk.create_session("session-inprocess", "sandbox")
            return f"Session created: {session['session_id']}. Running in-process (Mode 1)."

        # Handle session
        elif parsed_args.command == "session":
            sub = parsed_args.subcommand
            if sub == "create":
                res = await self.sdk.create_session("session-new", parsed_args.permission_mode)
                return json.dumps(res)
            elif sub == "status":
                res = await self.sdk.load_session(parsed_args.session_id)
                return json.dumps(res)
            elif sub == "follow":
                # Follow mode gets events stream via API
                events = await self.sdk.get_session_events(parsed_args.session_id)
                output = []
                for e in events:
                    output.append(f"[{e['timestamp']}] TOPIC: {e['topic']} | PAYLOAD: {json.dumps(e['payload'])}")
                return "\n".join(output) if output else "No events recorded."
            elif sub == "resume":
                res = await self.sdk.load_session(parsed_args.session_id)
                return f"Session {res['session_id']} resumed successfully."
            elif sub == "cancel":
                # Simulate session close/cancellation
                return f"Session {parsed_args.session_id} cancelled."

        # Handle task
        elif parsed_args.command == "task":
            sub = parsed_args.subcommand
            if sub == "list":
                # Call events to parse task logs
                events = await self.sdk.get_session_events(parsed_args.session_id)
                tasks = [e["payload"]["task_id"] for e in events if e["topic"] == "task.queued"]
                return json.dumps(tasks)

        # Handle agents
        elif parsed_args.command == "agents":
            sub = parsed_args.subcommand
            if sub == "list":
                events = await self.sdk.get_session_events(parsed_args.session_id)
                agents = [e["payload"]["agent_id"] for e in events if e["topic"] == "agent.created"]
                return json.dumps(agents)

        # Handle legacy orchestrator warnings compatibility
        elif parsed_args.command == "orchestrator":
            sub = parsed_args.subcommand
            warnings.warn(
                f"'orchestrator {sub}' daemon command is deprecated. Daemon Mode is optional and redirecting to Resident Service (Mode 3).",
                DeprecationWarning,
                stacklevel=2
            )
            return f"Legacy command '{parsed_args.command} {sub}' executed via Compatibility Adapter."

        return "Command not recognized."
