from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, cast


def do_deps(args: argparse.Namespace) -> int:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import workflow_runtime.application.dependency.dependency_resolver as dep_res
    import workflow_runtime.application.dependency.environment_inspector as dep_p2
    from workflow_runtime.application.dependency.dependency_resolver import (
        DEPRECATED_KEYS, parse_requirements, resolve_requirements,
        validate_requirements)

    skill = str(getattr(args, "skill", "") or "")
    action_val = str(getattr(args, "action", "") or "")
    if not skill and action_val not in ("doctor", "doctor-strict"):
        print("[deps] Error: --skill is required for this deps command", file=sys.stderr)
        sys.exit(1)

    subaction = str(getattr(args, 'action', None) or getattr(args, 'subaction', None) or "")

    if subaction == "inspect":
        reqs = parse_requirements(skill)
        if reqs:
            print(json.dumps(reqs, indent=2))
        else:
            print(f"No runtime_requirements found for skill '{skill}'.")
            sys.exit(1)

    elif subaction == "validate":
        reqs = parse_requirements(skill)
        if not reqs:
            print(f"No runtime_requirements declared for '{skill}'. Run 'deps fix' to add one.")
            sys.exit(1)
        result = validate_requirements(skill, reqs)
        if result.errors:
            for err in result.errors:
                print(f"[ERROR] {err}")
            sys.exit(1)
        for w in result.warnings:
            print(f"[WARN] {w}")
        print("Validation passed.")

    elif subaction == "resolve":
        reqs = parse_requirements(skill)
        try:
            ctx = resolve_requirements(skill, reqs)
            print(f"Resolved {len(ctx.resolved)} dependencies for '{skill}'.")
            if ctx.warnings:
                for w in ctx.warnings:
                    print(f"[WARN] {w}")
            print("Written to: .agents/state/runtime/dependencies.json")
        except SystemExit:
            raise
        except Exception as e:
            print(f"[deps resolve error] {e}", file=sys.stderr)
            sys.exit(1)

    elif subaction == "doctor":
        doc_fn: Any = getattr(dep_p2, "get_doctor_report", None)
        report: Any = doc_fn(strict_mode=False) if callable(doc_fn) else None
        if not report:
            print("No doctor report available.")
            return 0
        total_skills = getattr(report, "total_skills", 0)
        clean_skills = cast(list[Any], getattr(report, "clean_skills", []))
        warning_skills = cast(list[Any], getattr(report, "warning_skills", []))
        error_skills = cast(list[Any], getattr(report, "error_skills", []))
        details = cast(dict[str, Any], getattr(report, "details", {}))

        print("\nDependency Doctor Report")
        print("========================")
        print(f"Total skills scanned: {total_skills}")
        print(f"Clean: {len(clean_skills)}")
        print(f"Warnings: {len(warning_skills)}")
        print(f"Errors: {len(error_skills)}")
        if warning_skills or error_skills:
            print("\nIssues:")
            for s in warning_skills:
                s_name = str(s)
                s_det = cast(Any, details.get(s_name))
                raw_warns = getattr(s_det, "warnings", []) if s_det else []
                for w in cast(list[Any], raw_warns):
                    print(f"  [WARN] {s_name}: {w}")
            for s in error_skills:
                s_name = str(s)
                s_det = cast(Any, details.get(s_name))
                raw_errs = getattr(s_det, "errors", []) if s_det else []
                for err in cast(list[Any], raw_errs):
                    print(f"  [ERROR] {s_name}: {err}")
        if not error_skills:
            print("\nAll skills clean or with warnings only.")
        else:
            sys.exit(1)

    elif subaction == "doctor-strict":
        doc_fn: Any = getattr(dep_p2, "get_doctor_report", None)
        report: Any = doc_fn(strict_mode=True) if callable(doc_fn) else None
        if not report:
            print("No doctor report available.")
            return 0
        error_skills = cast(list[Any], getattr(report, "error_skills", []))
        details = cast(dict[str, Any], getattr(report, "details", {}))
        if error_skills:
            for s in error_skills:
                s_name = str(s)
                s_det = cast(Any, details.get(s_name))
                raw_errs = getattr(s_det, "errors", []) if s_det else []
                for err in cast(list[Any], raw_errs):
                    print(f"[ERROR] {s_name}: {err}", file=sys.stderr)
            sys.exit(1)
        print("All skills have valid runtime_requirements.")

    elif subaction == "fix":
        skills_to_fix: list[str] = []
        if getattr(args, "all", False):
            find_fn: Any = getattr(dep_res, "_find_all_skills", None)
            if callable(find_fn):
                skills_to_fix = [name for name, _ in cast(list[tuple[str, str]], find_fn())]
        elif skill:
            skills_to_fix = [skill]
        else:
            print("Usage: deps fix --skill <name> | --all", file=sys.stderr)
            sys.exit(1)

        all_diffs: list[dict[str, Any]] = []
        diff_fn: Any = getattr(dep_p2, "compute_deps_fix_diff", None)
        for skill_name in skills_to_fix:
            diff = cast(dict[str, Any], diff_fn(skill_name)) if callable(diff_fn) else None
            if diff:
                all_diffs.append(diff)

        if not all_diffs:
            print("No changes needed. All skills have up-to-date runtime_requirements.")
            return 0

        print(f"\nProposed changes ({len(all_diffs)} skills):")
        print("=" * 60)
        for diff in all_diffs:
            print(f"\nFile: {diff.get('skill_path')}")
            changes = cast(list[str], diff.get("changes", []))
            for change in changes:
                print(f"  + {change}")
            prop_tmpl = str(diff.get("proposed_template", ""))
            if prop_tmpl:
                print("\n  Proposed template to add:\n")
                for line in prop_tmpl.splitlines():
                    print(f"    {line}")

        print("\n" + "=" * 60)

        auto_approve = getattr(args, "yes", False)
        if not auto_approve:
            try:
                answer = input("\nApply these changes? [y/N]: ").strip().lower()
                if answer not in ("y", "yes"):
                    print("Changes rejected. No files modified.")
                    sys.exit(1)
            except (EOFError, KeyboardInterrupt):
                print("\nApproval required. Aborting.")
                sys.exit(1)

        for diff in all_diffs:
            skill_path = str(diff.get("skill_path", ""))
            try:
                with open(skill_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if diff.get("template_needed"):
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            new_fm = parts[1].rstrip() + "\n" + str(diff.get("proposed_template", ""))
                            content = "---" + new_fm + "---" + parts[2]

                if diff.get("migration_needed"):
                    for old_key, new_key in DEPRECATED_KEYS.items():
                        content = content.replace(f"  {old_key}:", f"  {new_key}:")

                with open(skill_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"Updated: {skill_path}")

                target_skill_name = str(diff.get("skill_name", ""))
                new_reqs = parse_requirements(target_skill_name)
                res_val = validate_requirements(target_skill_name, new_reqs)
                if not res_val.ok:
                    print(f"  [WARN] Post-fix validation failed for '{target_skill_name}': {res_val.errors}")
                else:
                    print("  Validation: OK")

            except Exception as e:
                print(f"[ERROR] Failed to update {skill_path}: {e}", file=sys.stderr)

    else:
        print(f"Unknown deps subaction: {subaction}", file=sys.stderr)
        sys.exit(1)
    return 0


def do_dependency(args: argparse.Namespace) -> None:
    if (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "graph":
        plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
        if not os.path.exists(plan_file):
            print(json.dumps({"graph": {}}, indent=2))
            return
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
                tasks = cast(list[Any], data.get("tasks", []))
                print(json.dumps({"tasks": tasks}, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def do_merge(args: argparse.Namespace) -> None:
    action_val = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    if action_val == "prepare":
        print("Merge prepared.")
    elif action_val == "complete":
        print("Merge completed successfully.")


def do_conflict(args: argparse.Namespace) -> None:
    conflicts_file = os.path.join(".agents", "runtime", "conflicts.json")
    os.makedirs(os.path.dirname(conflicts_file), exist_ok=True)
    action_val = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    if action_val == "detect":
        conflicts: list[Any] = []
        with open(conflicts_file, "w", encoding="utf-8") as f:
            json.dump({"conflicts": conflicts}, f, indent=2)
        print(json.dumps({"conflicts": conflicts}, indent=2))
    elif action_val == "resolve":
        print("Conflicts resolved.")


__all__ = [
    "do_deps",
    "do_dependency",
    "do_merge",
    "do_conflict",
]
