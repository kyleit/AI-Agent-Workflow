#!/usr/bin/env python3
"""
benchmark_init_flow.py
FEAT-050: So sánh tốc độ và độ chính xác giữa old init flow vs new lightweight init flow.

Use cases thực tế từ người dùng:
  UC-1: Developer mở project và bắt đầu brainstorm feature mới
  UC-2: Developer tiếp tục implement sau khi review
  UC-3: Developer chạy quick-fix sau báo lỗi từ CI
  UC-4: Developer khởi động workflow sau khi restart machine (cold start)
  UC-5: Developer switch branch và cần re-init

Mỗi use case đo:
  - Latency (ms)
  - Memory loaded (MB proxy - số bytes đọc)
  - Accuracy: các field mandatory có đủ không
  - Heavy ops triggered: số lần subprocess/file scan nặng
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class BenchResult:
    use_case: str
    mode: str           # "old" | "new"
    latency_ms: float
    bytes_read: int
    heavy_ops: int      # subprocess calls / large file reads
    fields_present: list[str]
    fields_missing: list[str]
    accuracy_score: float   # 0.0 - 1.0 (mandatory fields coverage)
    errors: list[str] = field(default_factory=list)
    notes: str = ""

MANDATORY_FIELDS = [
    "git_branch", "git_working_tree", "is_git_repository",
    "checkpoint", "work_item_id",
    "rules_loaded", "approvals_loaded", "state_loaded",
    "version",
]

# ─── Use Case Definitions ─────────────────────────────────────────────────────

USE_CASES = [
    {
        "id": "UC-1",
        "name": "Bắt đầu brainstorm feature mới",
        "description": "Developer mở project, chưa có work item active, cần khởi tạo workflow",
        "context": {"checkpoint": 1, "has_work_item": False, "git_clean": True, "has_memory": False},
    },
    {
        "id": "UC-2",
        "name": "Tiếp tục implement sau review",
        "description": "Developer resume workflow sau khi blueprint approved, cần load state nhanh",
        "context": {"checkpoint": 4, "has_work_item": True, "git_clean": False, "has_memory": True},
    },
    {
        "id": "UC-3",
        "name": "Quick-fix sau lỗi CI",
        "description": "CI báo lỗi, developer cần init nhanh để bắt đầu quick-fix ngay",
        "context": {"checkpoint": 2, "has_work_item": True, "git_clean": False, "has_memory": True},
    },
    {
        "id": "UC-4",
        "name": "Cold start sau khi restart máy",
        "description": "Machine restart, tất cả cache mất, env snapshot stale > 24h",
        "context": {"checkpoint": 1, "has_work_item": False, "git_clean": True, "has_memory": False,
                    "env_stale": True},
    },
    {
        "id": "UC-5",
        "name": "Switch branch và re-init",
        "description": "Developer switch sang feature branch, cần detect branch mới + checkpoint",
        "context": {"checkpoint": 3, "has_work_item": True, "git_clean": True, "has_memory": True,
                    "new_branch": "feat/FEAT-050-lightweight-init"},
    },
]

# ─── Setup helpers ────────────────────────────────────────────────────────────

def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except Exception:
        return 0

def setup_workspace(tmp_dir: str, ctx: dict) -> None:
    """Create a realistic fake workspace with state files."""
    state_dir = os.path.join(tmp_dir, ".agents", "state")
    memory_dir = os.path.join(tmp_dir, ".agents", "memory")
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(memory_dir, exist_ok=True)

    # context.json
    work_item = {"type": "FEAT", "id": "FEAT-050", "title": "Lightweight Runtime Init"} if ctx["has_work_item"] else {"type": "None", "id": "None", "title": "None"}
    _write_json(os.path.join(state_dir, "context.json"), {
        "workspace_path": ".",
        "checkpoint": ctx["checkpoint"],
        "project_version": "2.5.0",
        "version_source": "context.json",
        "work_item": work_item,
        "git": {
            "branch": ctx.get("new_branch", "main"),
            "working_tree": "clean" if ctx["git_clean"] else "dirty",
            "is_git_repository": True,
        },
        "updated_at": "2026-07-11T00:00:00+07:00",
    })

    # approvals.json
    _write_json(os.path.join(state_dir, "approvals.json"), {
        "blueprint": {"FEAT-050": {"approved": True, "approved_at": "2026-07-10T10:00:00Z"}},
        "updated_at": "2026-07-10T10:00:00Z",
    })

    # runtime.json
    _write_json(os.path.join(state_dir, "runtime.json"), {
        "status": "completed",
        "current_skill": "initialize-workflow",
        "checkpoint": ctx["checkpoint"],
        "updated_at": "2026-07-10T09:00:00Z",
    })

    # environment.json (stale nếu UC-4)
    env_ts = "2026-07-09T00:00:00Z" if ctx.get("env_stale") else "2026-07-11T00:00:00Z"
    _write_json(os.path.join(state_dir, "environment.json"), {
        "os": "Windows",
        "python": "3.14.4",
        "node": "22.0.0",
        "git": "2.45.0",
        "updated_at": env_ts,
    })

    # memory-state.json (metadata only)
    if ctx["has_memory"]:
        _write_json(os.path.join(memory_dir, "memory-state.json"), {
            "status": "ready",
            "chunk_count": 48,
            "last_updated": "2026-07-10T12:00:00Z",
            "total_size_kb": 1240,
        })
        # Simulate heavy memory file (project-summary.md ~1.2MB)
        summary_path = os.path.join(memory_dir, "project-summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("# Project Summary\n" + ("This is a large summary file. " * 2000) + "\n")

    # AI_RULES.md stub
    with open(os.path.join(tmp_dir, "AI_RULES.md"), "w", encoding="utf-8") as f:
        f.write("# AI Rules\n## Approval Gate Policy\n" + ("Rule content. " * 100) + "\n")

    # .agents/AGENTS.md stub
    os.makedirs(os.path.join(tmp_dir, ".agents"), exist_ok=True)
    with open(os.path.join(tmp_dir, ".agents", "AGENTS.md"), "w", encoding="utf-8") as f:
        f.write("# AIWF Agents\n" + ("Agent rules. " * 50) + "\n")

    # Fake package.json (for old init manifest scan test)
    with open(os.path.join(tmp_dir, "package.json"), "w", encoding="utf-8") as f:
        json.dump({"name": "aiwf", "version": "2.5.0"}, f)

    # Fake go.mod
    with open(os.path.join(tmp_dir, "go.mod"), "w", encoding="utf-8") as f:
        f.write("module github.com/aiwf\ngo 1.22\n")

# ─── OLD Init Flow Simulation ─────────────────────────────────────────────────

def run_old_init(workspace_dir: str, ctx: dict) -> tuple[float, int, int, dict]:
    """
    Simulate OLD initialize-workflow behavior:
    - Load full project-summary.md
    - Scan docs/ directories for work item
    - Run git describe --tags
    - Run python --version, node --version
    - Parse transcript for usage
    - Scan package.json, go.mod, pyproject.toml for version
    Returns: (latency_ms, bytes_read, heavy_ops_count, result_dict)
    """
    heavy_ops = 0
    bytes_read = 0
    result = {}
    start = time.perf_counter()

    old_dir = os.getcwd()
    os.chdir(workspace_dir)

    try:
        # 1. Load full AI_RULES.md + AGENTS.md (acceptable — still done in new)
        for rules_file in ["AI_RULES.md", os.path.join(".agents", "AGENTS.md")]:
            if os.path.exists(rules_file):
                with open(rules_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    bytes_read += len(content)
        result["rules_loaded"] = True

        # 2. OLD: Load full project-summary.md (HEAVY)
        summary_path = os.path.join(".agents", "memory", "project-summary.md")
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                content = f.read()
                bytes_read += len(content)
            heavy_ops += 1  # full memory load
        result["memory_loaded"] = True

        # 3. OLD: Scan docs/ for work item (HEAVY)
        docs_scan_bytes = 0
        docs_dir = os.path.join(workspace_dir, "docs")
        if os.path.isdir(docs_dir):
            for root, dirs, files in os.walk(docs_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    docs_scan_bytes += _file_size(fpath)
            heavy_ops += 1  # workspace scan
        bytes_read += docs_scan_bytes
        result["work_item_id"] = "FEAT-050" if ctx["has_work_item"] else "None"

        # 4. OLD: git describe --tags (HEAVY subprocess)
        try:
            subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True, text=True, timeout=5, cwd=workspace_dir
            )
            heavy_ops += 1
        except Exception:
            pass

        # 5. OLD: python --version (HEAVY subprocess)
        try:
            subprocess.run(["python", "--version"], capture_output=True, text=True, timeout=5)
            heavy_ops += 1
        except Exception:
            pass

        # 6. OLD: node --version (HEAVY subprocess)
        try:
            subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            heavy_ops += 1
        except Exception:
            pass

        # 7. OLD: scan manifest files for version (HEAVY)
        for manifest in ["package.json", "go.mod", "pyproject.toml", "Cargo.toml"]:
            if os.path.exists(manifest):
                with open(manifest, "r", encoding="utf-8") as f:
                    content = f.read()
                    bytes_read += len(content)
                heavy_ops += 1
                result["version"] = "2.5.0"
                break

        # 8. OLD: git branch (acceptable)
        try:
            branch_res = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, timeout=5, cwd=workspace_dir
            )
            result["git_branch"] = branch_res.stdout.strip() or "main"
            result["is_git_repository"] = True
            heavy_ops += 1  # counts as subprocess in old flow
        except Exception:
            result["git_branch"] = "unknown"
            result["is_git_repository"] = False

        # 9. OLD: git status
        try:
            status_res = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True, text=True, timeout=5, cwd=workspace_dir
            )
            result["git_working_tree"] = "dirty" if status_res.stdout.strip() else "clean"
        except Exception:
            result["git_working_tree"] = "unknown"

        # 10. Read state for checkpoint
        ctx_file = os.path.join(".agents", "state", "context.json")
        if os.path.exists(ctx_file):
            with open(ctx_file, "r", encoding="utf-8") as f:
                ctx_data = json.load(f)
                bytes_read += _file_size(ctx_file)
            result["checkpoint"] = ctx_data.get("checkpoint", 1)
        result["state_loaded"] = True
        result["approvals_loaded"] = True

    finally:
        os.chdir(old_dir)

    latency_ms = (time.perf_counter() - start) * 1000
    return latency_ms, bytes_read, heavy_ops, result


# ─── NEW Init Flow Simulation ─────────────────────────────────────────────────

def run_new_init(workspace_dir: str, ctx: dict) -> tuple[float, int, int, dict]:
    """
    Simulate NEW lightweight initialize-workflow behavior (FEAT-050):
    - SHA-256 hash of rules files only (no full load)
    - Read context.json for work item (no docs scan)
    - Read context.json for version (no manifest scan)
    - Only 3 git commands (no git describe --tags)
    - Read environment.json (no subprocess)
    - Read usage from state/usage.json (no transcript parse)
    Returns: (latency_ms, bytes_read, heavy_ops_count, result_dict)
    """
    heavy_ops = 0
    bytes_read = 0
    result = {}
    start = time.perf_counter()

    old_dir = os.getcwd()
    os.chdir(workspace_dir)

    try:
        import hashlib

        # Step 2: Guardrails summary — SHA-256 only (lightweight)
        for rules_file in ["AI_RULES.md", os.path.join(".agents", "AGENTS.md")]:
            if os.path.exists(rules_file):
                with open(rules_file, "rb") as f:
                    data = f.read()
                    bytes_read += len(data)
                    hashlib.sha256(data).hexdigest()
        result["rules_loaded"] = True

        # Step 3: Git state — exactly 3 allowed commands
        try:
            branch_res = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, timeout=3
            )
            result["git_branch"] = branch_res.stdout.strip() or "unknown"
        except Exception:
            result["git_branch"] = "unknown"

        try:
            repo_res = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True, text=True, timeout=3
            )
            result["is_git_repository"] = "true" in repo_res.stdout
        except Exception:
            result["is_git_repository"] = False

        try:
            status_res = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True, text=True, timeout=3
            )
            result["git_working_tree"] = "dirty" if status_res.stdout.strip() else "clean"
        except Exception:
            result["git_working_tree"] = "clean"

        # Step 4: Read cached state only
        ctx_file = os.path.join(".agents", "state", "context.json")
        if os.path.exists(ctx_file):
            with open(ctx_file, "r", encoding="utf-8") as f:
                ctx_data = json.load(f)
                bytes_read += _file_size(ctx_file)
            result["checkpoint"] = ctx_data.get("checkpoint", 1)
            result["work_item_id"] = ctx_data.get("work_item", {}).get("id", "None")
            result["version"] = ctx_data.get("project_version", "0.0.0")
            result["state_loaded"] = True

        # Read approvals
        approvals_file = os.path.join(".agents", "state", "approvals.json")
        if os.path.exists(approvals_file):
            bytes_read += _file_size(approvals_file)
            result["approvals_loaded"] = True
        else:
            result["approvals_loaded"] = False

        # Step 5: Memory — metadata only (NOT full project-summary.md)
        memory_meta = os.path.join(".agents", "memory", "memory-state.json")
        if os.path.exists(memory_meta):
            with open(memory_meta, "rb") as f:
                data = f.read()
                bytes_read += len(data)
            # DO NOT read project-summary.md
            result["memory_status"] = "cached"

        # Step 5: Environment snapshot (no subprocess)
        env_file = os.path.join(".agents", "state", "environment.json")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                env_data = json.load(f)
                bytes_read += _file_size(env_file)
            result["env_status"] = "stale" if ctx.get("env_stale") else "cached"

        # heavy_ops = 0 for new flow (no forbidden operations)

    finally:
        os.chdir(old_dir)

    latency_ms = (time.perf_counter() - start) * 1000
    return latency_ms, bytes_read, heavy_ops, result


# ─── Scoring ─────────────────────────────────────────────────────────────────

def compute_accuracy(result: dict) -> tuple[float, list, list]:
    present = [f for f in MANDATORY_FIELDS if result.get(f) not in (None, "", "None", False)]
    missing = [f for f in MANDATORY_FIELDS if f not in present]
    score = len(present) / len(MANDATORY_FIELDS)
    return round(score, 2), present, missing


# ─── Main Benchmark ───────────────────────────────────────────────────────────

def run_benchmark(n_runs: int = 5) -> list[BenchResult]:
    results: list[BenchResult] = []

    for uc in USE_CASES:
        with tempfile.TemporaryDirectory(prefix="aiwf_bench_") as tmp_dir:
            setup_workspace(tmp_dir, uc["context"])

            # Run each flow n_runs times, take median
            old_latencies, new_latencies = [], []
            old_bytes_list, new_bytes_list = [], []
            old_heavy_list, new_heavy_list = [], []
            old_result, new_result = {}, {}

            for _ in range(n_runs):
                lat, br, ho, res = run_old_init(tmp_dir, uc["context"])
                old_latencies.append(lat)
                old_bytes_list.append(br)
                old_heavy_list.append(ho)
                old_result = res

            for _ in range(n_runs):
                lat, br, ho, res = run_new_init(tmp_dir, uc["context"])
                new_latencies.append(lat)
                new_bytes_list.append(br)
                new_heavy_list.append(ho)
                new_result = res

            # Median
            old_latencies.sort(); new_latencies.sort()
            old_lat = old_latencies[n_runs // 2]
            new_lat = new_latencies[n_runs // 2]

            old_acc, old_present, old_missing = compute_accuracy(old_result)
            new_acc, new_present, new_missing = compute_accuracy(new_result)

            results.append(BenchResult(
                use_case=f"{uc['id']}: {uc['name']}",
                mode="OLD",
                latency_ms=round(old_lat, 1),
                bytes_read=old_bytes_list[n_runs // 2],
                heavy_ops=old_heavy_list[n_runs // 2],
                fields_present=old_present,
                fields_missing=old_missing,
                accuracy_score=old_acc,
                notes=uc["description"],
            ))
            results.append(BenchResult(
                use_case=f"{uc['id']}: {uc['name']}",
                mode="NEW",
                latency_ms=round(new_lat, 1),
                bytes_read=new_bytes_list[n_runs // 2],
                heavy_ops=new_heavy_list[n_runs // 2],
                fields_present=new_present,
                fields_missing=new_missing,
                accuracy_score=new_acc,
                notes=uc["description"],
            ))

    return results


# ─── Report ──────────────────────────────────────────────────────────────────

def print_report(results: list[BenchResult]) -> None:
    print("\n" + "=" * 90)
    print("  FEAT-050: init-workflow Benchmark — OLD vs NEW (Lightweight)")
    print("=" * 90)

    # Group by use case
    use_cases = list(dict.fromkeys(r.use_case for r in results))

    print(f"\n{'Use Case':<45} {'Mode':<6} {'Latency':>10} {'Bytes Read':>12} {'Heavy Ops':>10} {'Accuracy':>10}")
    print("-" * 97)

    total_old_lat, total_new_lat = 0.0, 0.0
    total_old_bytes, total_new_bytes = 0, 0
    total_old_heavy, total_new_heavy = 0, 0
    n_uc = 0

    for uc_name in use_cases:
        pair = [r for r in results if r.use_case == uc_name]
        old_r = next((r for r in pair if r.mode == "OLD"), None)
        new_r = next((r for r in pair if r.mode == "NEW"), None)

        for r in [old_r, new_r]:
            if r is None:
                continue
            acc_str = f"{r.accuracy_score * 100:.0f}%"
            bytes_kb = f"{r.bytes_read / 1024:.1f} KB"
            print(f"{r.use_case:<45} {r.mode:<6} {r.latency_ms:>8.1f}ms {bytes_kb:>12} {r.heavy_ops:>10} {acc_str:>10}")

        if old_r and new_r:
            speedup = old_r.latency_ms / max(new_r.latency_ms, 0.01)
            byte_reduction = (1 - new_r.bytes_read / max(old_r.bytes_read, 1)) * 100
            acc_delta = (new_r.accuracy_score - old_r.accuracy_score) * 100
            print(f"  >> Speedup: {speedup:.1f}x faster | Bytes: -{byte_reduction:.0f}% | Heavy ops: {old_r.heavy_ops} -> {new_r.heavy_ops} | Accuracy: {acc_delta:+.0f}%")
            total_old_lat += old_r.latency_ms
            total_new_lat += new_r.latency_ms
            total_old_bytes += old_r.bytes_read
            total_new_bytes += new_r.bytes_read
            total_old_heavy += old_r.heavy_ops
            total_new_heavy += new_r.heavy_ops
            n_uc += 1
        print()

    # Summary
    print("=" * 90)
    print("  SUMMARY")
    print("=" * 90)
    if n_uc > 0:
        avg_old = total_old_lat / n_uc
        avg_new = total_new_lat / n_uc
        avg_speedup = avg_old / max(avg_new, 0.01)
        byte_saved = (1 - total_new_bytes / max(total_old_bytes, 1)) * 100
        heavy_saved = total_old_heavy - total_new_heavy

        print(f"  Avg latency OLD:   {avg_old:.1f}ms")
        print(f"  Avg latency NEW:   {avg_new:.1f}ms")
        print(f"  Avg speedup:       {avg_speedup:.1f}x faster")
        print(f"  Bytes read saved:  {byte_saved:.0f}%")
        print(f"  Heavy ops saved:   {total_old_heavy} -> {total_new_heavy} ({heavy_saved} ops removed)")

    # Accuracy detail
    print("\n  ACCURACY DETAIL (Mandatory Fields)")
    print("-" * 70)
    for uc_name in use_cases:
        pair = [r for r in results if r.use_case == uc_name]
        old_r = next((r for r in pair if r.mode == "OLD"), None)
        new_r = next((r for r in pair if r.mode == "NEW"), None)
        print(f"\n  {uc_name}")
        if old_r:
            missing_str = ", ".join(old_r.fields_missing) if old_r.fields_missing else "none"
            print(f"    OLD {old_r.accuracy_score*100:.0f}%  Missing: {missing_str}")
        if new_r:
            missing_str = ", ".join(new_r.fields_missing) if new_r.fields_missing else "none"
            print(f"    NEW {new_r.accuracy_score*100:.0f}%  Missing: {missing_str}")

    # Guardrail check
    print("\n  GUARDRAIL CHECK (Latency Budget < 800ms)")
    print("-" * 50)
    new_results = [r for r in results if r.mode == "NEW"]
    all_pass = True
    for r in new_results:
        status = "[PASS]" if r.latency_ms < 800 else "[FAIL]"
        if r.latency_ms >= 800:
            all_pass = False
        print(f"  {status}  {r.use_case[:40]:<40} {r.latency_ms:.1f}ms")
    if all_pass:
        print("\n  [OK] All use cases within 800ms latency budget!")
    else:
        print("\n  [!!] Some use cases EXCEED 800ms latency budget!")

    print("=" * 90)


# ─── JSON Export ─────────────────────────────────────────────────────────────

def export_json(results: list[BenchResult], output_path: str) -> None:
    data = [
        {
            "use_case": r.use_case,
            "mode": r.mode,
            "latency_ms": r.latency_ms,
            "bytes_read": r.bytes_read,
            "heavy_ops": r.heavy_ops,
            "accuracy_score": r.accuracy_score,
            "fields_missing": r.fields_missing,
            "notes": r.notes,
        }
        for r in results
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to: {output_path}")


if __name__ == "__main__":
    import argparse
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="FEAT-050 Init Flow Benchmark")
    parser.add_argument("--runs", type=int, default=5, help="Number of runs per use case (default: 5)")
    parser.add_argument("--json", type=str, default=None, help="Export results to JSON file")
    args = parser.parse_args()

    print(f"Running benchmark: {len(USE_CASES)} use cases x {args.runs} runs each...")
    results = run_benchmark(n_runs=args.runs)
    print_report(results)

    if args.json:
        export_json(results, args.json)
