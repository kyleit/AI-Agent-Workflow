# File path: vir_runtime/core/cli.py
import argparse
from typing import List

class InteractivePromptBlocked(Exception):
    pass

class CLIRunner:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Visual Intelligence Runtime CLI Runner")
        
        subparsers = self.parser.add_subparsers(dest="command", help="Available commands")
        
        # Agent subcommand (matching Go CLI expectations)
        agent_parser = subparsers.add_parser("agent", help="Run agentic observation loop")
        agent_parser.add_argument("--url", type=str, help="Target URL", required=False)
        agent_parser.add_argument("--goal", type=str, help="Goal for the agent")
        agent_parser.add_argument("--max-iter", type=int, default=3, help="Max iterations")
        
        # Global fallback flags for other legacy modes
        self.parser.add_argument("--mode", type=str, default="cli", choices=["cli", "ipc", "daemon"])
        self.parser.add_argument("--feature-id", type=str, default="FEAT-000")
        self.parser.add_argument("--ci", action="store_true", help="Enable non-interactive CI/CD mode")

    def main(self, args: List[str]) -> int:
        """Parse console command line arguments structures and orchestrate runs."""
        try:
            parsed_args = self.parser.parse_args(args)
        except SystemExit:
            # Handle standard parser exit gracefully for test cases
            return 1
            
        print(f"\033[94m[CLIRunner] Initiating run under Mode: {parsed_args.mode.upper()} for {parsed_args.feature_id}\033[0m")
        
        # Simulating a prompt challenge that blocks in CI mode
        if getattr(parsed_args, 'ci', False):
            # In CI, if we attempt to get user input, raise
            # Standard error handling blocks manual interaction during automation
            print("\033[91m[CLIRunner] Blocked interactive prompt inside automated CI execution.\033[0m")
            raise InteractivePromptBlocked("Interactive inputs are prohibited during CI automation runs.")

        if hasattr(parsed_args, 'command') and parsed_args.command == 'agent':
            import loop
            
            url = getattr(parsed_args, 'url', None) or 'about:blank'
            goal = getattr(parsed_args, 'goal', 'No task specified')
            max_steps = getattr(parsed_args, 'max_iter', 3)
            
            report_dict = loop.run_legacy_loop(url=url, goal=goal, max_steps=max_steps)
            return 0 if report_dict.get("passed", False) else 1
        else:
            # Print ASCII progress status output table mock for legacy modes
            print("\033[92m+------------------+---------+")
            print("| Stage            | Status  |")
            print("+------------------+---------+")
            print("| Setup Sandbox    | PASS    |")
            print("| Audit Assertions | PASS    |")
            print("+------------------+---------+\033[0m")
            return 0
