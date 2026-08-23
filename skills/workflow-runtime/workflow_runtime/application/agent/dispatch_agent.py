from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

AGENTS_DIR_CANDIDATES = [
    Path("agents"),
    Path(".agents/agents"),
]

AGY_MODEL = "gemini-3.6-flash-high"
AGY_DEFAULT_EFFORT = "high"
AGY_DEFAULT_TIMEOUT = "15m"


def find_agents_dir() -> Path:
    """Find the agents directory, preferring the primary location."""
    for candidate in AGENTS_DIR_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find agents/ directory. Searched: {[str(c) for c in AGENTS_DIR_CANDIDATES]}"
    )


def get_project_root() -> str:
    """Resolve the git project root dynamically (no hardcoded paths)."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError("Not inside a git repository. Run from within the project directory.")
    return result.stdout.strip()


def parse_frontmatter(md_path: Path) -> dict[str, str]:
    """Parse YAML frontmatter from a markdown file."""
    content = md_path.read_text(encoding="utf-8")

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    frontmatter_text = match.group(1)
    data: dict[str, str] = {}

    prompt_match = re.search(r"agy_system_prompt:\s*\|(.+?)(?=\n\w|\Z)", frontmatter_text, re.DOTALL)
    if prompt_match:
        raw = prompt_match.group(1)
        lines = raw.split("\n")
        cleaned = "\n".join(line[2:] if line.startswith("  ") else line for line in lines)
        data["agy_system_prompt"] = cleaned.strip()

    for field in ["id", "display_name", "role", "description"]:
        m = re.search(rf'^{field}:\s*"?([^"\n]+)"?', frontmatter_text, re.MULTILINE)
        if m:
            data[field] = m.group(1).strip()

    return data


def list_roles(agents_dir: Path) -> None:
    """Print all available agent roles."""
    print(f"\n{'Role':<30} {'Display Name':<25} {'Category'}")
    print("-" * 80)

    for md_file in sorted(agents_dir.glob("*.md")):
        if md_file.name in ("README.md",):
            continue
        data = parse_frontmatter(md_file)
        role_id = data.get("id", md_file.stem)
        display = data.get("display_name", role_id)
        desc = data.get("role", "")[:50]
        print(f"{role_id:<30} {display:<25} {desc}")
    print()


def build_prompt(system_prompt: str, task: str, replacements: dict[str, str]) -> str:
    """
    Build the final prompt by applying context replacements.
    """
    prompt = system_prompt

    for placeholder, value in replacements.items():
        if value:
            prompt = prompt.replace(placeholder, value)

    if task:
        prompt = prompt + f"\n\nCurrent task from coordinator:\n{task}"

    return prompt


def dispatch(role: str, task: str, replacements: dict[str, str], timeout: str, effort: str, dry_run: bool) -> None:
    """Load the agent role and dispatch to agy."""
    agents_dir = find_agents_dir()
    project_root = get_project_root()

    role_file = agents_dir / f"{role}.md"
    if not role_file.exists():
        alt = agents_dir / f"{role.replace('-', '_')}.md"
        if alt.exists():
            role_file = alt
        else:
            available = [f.stem for f in agents_dir.glob("*.md") if f.name != "README.md"]
            raise FileNotFoundError(
                f"Agent role '{role}' not found.\nAvailable roles: {', '.join(sorted(available))}"
            )

    agent_data = parse_frontmatter(role_file)

    if "agy_system_prompt" not in agent_data:
        raise ValueError(
            f"Agent '{role}' has no agy_system_prompt in frontmatter. "
            f"Add an agy_system_prompt field to {role_file}."
        )

    system_prompt = agent_data["agy_system_prompt"]
    final_prompt = build_prompt(system_prompt, task, replacements)

    display_name = str(agent_data.get("display_name", role))
    print(f"\n{'='*60}")
    print(f"  Dispatching: {display_name} ({role})")
    print(f"  Project:     {project_root}")
    print(f"  Agent file:  {role_file}")
    print(f"  Effort:      {effort}  Timeout: {timeout}")
    print(f"{'='*60}\n")

    cmd = [
        "agy",
        "--model", AGY_MODEL,
        "--effort", effort,
        "--dangerously-skip-permissions",
        "--add-dir", project_root,
        "--print-timeout", timeout,
        "--print", final_prompt,
    ]

    if dry_run:
        print("DRY RUN — agy command that would be executed:")
        print(f"  agy \\")
        print(f"    --model {AGY_MODEL} \\")
        print(f"    --effort {effort} \\")
        print(f"    --dangerously-skip-permissions \\")
        print(f"    --add-dir \"{project_root}\" \\")
        print(f"    --print-timeout {timeout} \\")
        print(f"    --print \"[{len(final_prompt)} chars — prompt omitted in dry run]\"")
        print(f"\nFirst 500 chars of prompt:\n{final_prompt[:500]}\n")
        return

    try:
        result = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("ERROR: 'agy' binary not found on PATH.")
        print("Install it from: https://antigravity.dev/docs/cli")
        print("\nFallback: copy the prompt above and paste it to Antigravity IDE manually.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDispatch cancelled by user.")
        sys.exit(130)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIWF Multi-Agent Dispatcher — invokes agy with the correct role prompt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--role", "-r", help="Agent role to dispatch (e.g., planner, architect, coder)")
    parser.add_argument("--task", "-t", default="", help="User task description")
    parser.add_argument("--blueprint-path", "-b", default="", help="Path to Blueprint file")
    parser.add_argument("--plan-path", "-p", default="", help="Path to Plan file")
    parser.add_argument("--report-path", default="", help="Path to Auditor report (for manager role)")
    parser.add_argument("--auditor-report", default="", help="Alias for --report-path")
    parser.add_argument("--spec-path", "-s", default="", help="Path to Spec file")
    parser.add_argument("--timeout", default=AGY_DEFAULT_TIMEOUT, help="AGY timeout (default: 15m)")
    parser.add_argument("--effort", choices=["low", "medium", "high"], default=AGY_DEFAULT_EFFORT)
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing")
    parser.add_argument("--list", "-l", action="store_true", help="List all available agent roles")

    args = parser.parse_args()

    if args.list:
        agents_dir = find_agents_dir()
        list_roles(agents_dir)
        return

    if not args.role:
        parser.print_help()
        print("\nERROR: --role is required. Use --list to see available roles.")
        sys.exit(1)

    report_path = str(args.report_path or args.auditor_report or "")
    blueprint_path = str(args.blueprint_path or "")
    plan_path = str(args.plan_path or "")
    spec_path = str(args.spec_path or "")
    task_desc = str(args.task or "")
    timeout_val = str(args.timeout or AGY_DEFAULT_TIMEOUT)
    effort_val = str(args.effort or AGY_DEFAULT_EFFORT)
    dry_run_val = bool(args.dry_run)
    role_val = str(args.role)

    replacements = {
        "<BLUEPRINT_PATH>": blueprint_path,
        "<PLAN_PATH>": plan_path,
        "<SPEC_PATH>": spec_path,
        "<AUDITOR_REPORT_PATH>": report_path,
        "<MANAGER_REPORT_PATH>": report_path,
        "<INSERT REQUEST HERE>": task_desc,
        "<ARTIFACT_PATH>": blueprint_path or plan_path,
        "<FRONTEND_SOURCE_PATH>": "",
    }

    dispatch(
        role=role_val,
        task=task_desc,
        replacements=replacements,
        timeout=timeout_val,
        effort=effort_val,
        dry_run=dry_run_val,
    )


if __name__ == "__main__":
    main()
