"""Python VAR (Visual Agentic Runtime) CLI Dispatcher Bridge.

Routes subcommands ('run', 'agent', 'audit', 'check') to vir_runtime.varbc services.
"""

import os
import sys
import json
import argparse
import asyncio
from typing import List, Dict, Any

# Ensure script directory is in sys.path for vir_runtime package imports
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from vir_runtime.varbc.infrastructure.baseline_repo import FileBaselineRepo
from vir_runtime.varbc.infrastructure.report_repo import FileReportRepo
from vir_runtime.varbc.infrastructure.cdp import AsyncCDPClient
from vir_runtime.varbc.infrastructure.gemini_provider import GeminiVisionProvider
from vir_runtime.varbc.application.service import VARService
from vir_runtime.varbc.application.agent import VARAgentLoop
from vir_runtime.varbc.application.investigator import VARInvestigator
from vir_runtime.varbc.application.verifier import VARVerifier


def create_parser() -> argparse.ArgumentParser:
    """Constructs ArgumentParser with subcommands for CLI bridge."""
    parser = argparse.ArgumentParser(
        prog="var_dispatch",
        description="Python VAR (Visual Agentic Runtime) CLI Dispatcher Bridge",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Target subcommand")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Capture visual observation")
    run_parser.add_argument("--url", required=True, help="Target page URL")
    run_parser.add_argument("--selector", default="body", help="CSS selector")

    # Command: agent
    agent_parser = subparsers.add_parser("agent", help="Run autonomous agent loop")
    agent_parser.add_argument("--url", required=True, help="Starting URL")
    agent_parser.add_argument("--goal", required=True, help="User objective goal")
    agent_parser.add_argument("--max-steps", type=int, default=10, help="Max steps")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Run RCA investigation")
    audit_parser.add_argument("--report-id", required=True, help="Target report ID")

    # Command: check
    check_parser = subparsers.add_parser("check", help="Run Quality Gate verification")
    check_parser.add_argument("--baseline", required=True, help="Baseline component ID")
    check_parser.add_argument("--current", required=True, help="Current observation ID")

    return parser


async def main_async(args: argparse.Namespace) -> int:
    """Asynchronous entrypoint routing subcommands to vir_runtime.varbc services."""
    baseline_repo = FileBaselineRepo()
    report_repo = FileReportRepo()
    cdp_client = AsyncCDPClient()
    service = VARService(cdp_client, baseline_repo, report_repo)

    if args.subcommand == "run":
        obs, _ = await service.capture_screenshot(args.url, args.selector)
        print(obs.model_dump_json())
        return 0

    if args.subcommand == "agent":
        llm_provider = GeminiVisionProvider()
        investigator = VARInvestigator()
        verifier = VARVerifier()
        loop = VARAgentLoop(
            cdp_client,
            llm_provider,
            report_repo,
            investigator,
            verifier,
            max_steps=args.max_steps,
        )
        report = await loop.run(args.url, args.goal)
        print(report.model_dump_json())
        return 0 if report.passed else 1

    if args.subcommand == "audit":
        investigator = VARInvestigator()
        report = await report_repo.get_report(args.report_id)
        if report is None:
            sys.stderr.write(f"Report not found: {args.report_id}\n")
            return 1
        investigation = await investigator.investigate(report.observations)
        print(investigation.model_dump_json())
        return 0

    if args.subcommand == "check":
        verifier = VARVerifier()
        report = await service.generate_report([], [])
        print(report.model_dump_json())
        return 0 if report.passed else 1

    return 1


def main() -> None:
    """Synchronous main wrapper executing main_async via asyncio.run()."""
    parser = create_parser()
    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        sys.exit(1)
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
