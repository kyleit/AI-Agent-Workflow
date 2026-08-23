"""
workflow_runtime/presentation/cli/benchmark_exporter.py

JSON exporter and CLI entrypoint for FEAT-050 Init Flow Benchmark results.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from workflow_runtime.presentation.cli.benchmark_init_flow import (
    USE_CASES, BenchResult, print_report, run_benchmark)


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


def main() -> None:
    parser = argparse.ArgumentParser(description="FEAT-050 Init Flow Benchmark")
    parser.add_argument("--runs", type=int, default=5, help="Number of runs per use case (default: 5)")
    parser.add_argument("--json", type=str, default=None, help="Export results to JSON file")
    args = parser.parse_args()

    n_runs = int(getattr(args, "runs", 5))
    json_path = getattr(args, "json", None)

    print(f"Running benchmark: {len(USE_CASES)} use cases x {n_runs} runs each...")
    results = run_benchmark(n_runs=n_runs)
    print_report(results)

    if json_path:
        export_json(results, str(json_path))


if __name__ == "__main__":
    main()


__all__ = ["export_json", "main"]
