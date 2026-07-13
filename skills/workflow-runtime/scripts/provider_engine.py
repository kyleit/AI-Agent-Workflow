#!/usr/bin/env python3
# provider_engine.py
# Standalone CLI: detect / parse / pricing / diagnose
# Sole entry point for all provider operations.
# Does NOT import workflow_runtime.py or any AIWF-specific modules.
from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure the scripts directory is importable when called from any working directory
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _build_registry():
    """Build ConnectorRegistry with all enabled connectors."""
    from connectors import build_default_registry
    return build_default_registry()


def _get_cost_engine():
    """Return module-level CostEngine singleton."""
    from cost_engine import cost_engine
    return cost_engine


# ------------------------------------------------------------------ #
#  Subcommand: detect                                                  #
# ------------------------------------------------------------------ #

def cmd_detect(args) -> int:
    """Detect all installed providers and output JSON."""
    try:
        registry = _build_registry()
        detected = registry.detect_all()
        output = [
            {
                "provider": d.provider_name,
                "path": d.path,
                "version": d.version,
                "status": d.status,
                "error": d.error,
            }
            for d in detected
        ]
        print(json.dumps(output, ensure_ascii=False))
        return 0
    except Exception as exc:
        sys.stderr.write(f"[provider_engine detect] Error: {exc}\n")
        return 1


# ------------------------------------------------------------------ #
#  Subcommand: parse                                                   #
# ------------------------------------------------------------------ #

def cmd_parse(args) -> int:
    """Parse usage data for a provider/conversation and output JSON."""
    provider_name = args.provider
    conv_id = args.conv_id

    if not provider_name:
        sys.stderr.write("[provider_engine parse] --provider is required\n")
        return 1
    if not conv_id:
        sys.stderr.write("[provider_engine parse] --conv-id is required\n")
        return 1

    try:
        registry = _build_registry()
    except Exception as exc:
        sys.stderr.write(f"[provider_engine parse] Registry init error: {exc}\n")
        return 1

    connector = registry.get_connector(provider_name)
    if connector is None:
        sys.stderr.write(
            f"[provider_engine parse] Connector not found: '{provider_name}'. "
            f"Registered: {registry.list_registered()}\n"
        )
        return 1

    try:
        records = connector.parse_conversation(conv_id)
    except PermissionError as exc:
        sys.stderr.write(f"[provider_engine parse] Permission error: {exc}\n")
        return 2
    except Exception as exc:
        sys.stderr.write(f"[provider_engine parse] Parse error: {exc}\n")
        return 1

    # Apply cost engine to each record
    engine = _get_cost_engine()
    enriched = []
    for rec in records:
        cost_result = engine.calculate(
            provider=rec.provider,
            model=rec.model,
            input_tokens=rec.input_tokens,
            output_tokens=rec.output_tokens,
            cache_read_tokens=rec.cache_read_tokens,
            cache_write_tokens=rec.cache_write_tokens,
            thinking_tokens=rec.thinking_tokens,
        )
        d = rec.to_dict()
        d["estimated_cost_usd"] = cost_result.cost_usd
        d.pop("raw_payload", None)  # omit from CLI output (too verbose)
        enriched.append(d)

    # Determine overall accuracy_source
    sources = {r.get("accuracy_source", "unknown") for r in enriched}
    overall_source = "unknown"
    priority = [
        "provider_reported", "transcript_parsed", "derived", "estimated", "unknown"
    ]
    for p in priority:
        if p in sources:
            overall_source = p
            break

    output = {
        "provider": provider_name,
        "conversation_id": conv_id,
        "records_count": len(enriched),
        "accuracy_source": overall_source,
        "pricing_version": engine.get_version(),
        "pricing_stale": engine.is_stale(30),
        "records": enriched,
    }
    print(json.dumps(output, ensure_ascii=False, default=str))
    return 0


# ------------------------------------------------------------------ #
#  Subcommand: pricing                                                 #
# ------------------------------------------------------------------ #

def cmd_pricing(args) -> int:
    """Calculate cost for a provider/model/token combination."""
    try:
        engine = _get_cost_engine()
        result = engine.calculate(
            provider=args.provider,
            model=args.model,
            input_tokens=int(args.input or 0),
            output_tokens=int(args.output or 0),
            cache_read_tokens=int(args.cache_read or 0),
            cache_write_tokens=int(args.cache_write or 0),
            thinking_tokens=int(args.thinking or 0),
        )
        print(json.dumps(engine.to_dict(result), ensure_ascii=False))
        return 0
    except Exception as exc:
        sys.stderr.write(f"[provider_engine pricing] Error: {exc}\n")
        return 1


# ------------------------------------------------------------------ #
#  Subcommand: diagnose                                                #
# ------------------------------------------------------------------ #

def cmd_diagnose(args) -> int:
    """Run diagnostics on all providers and output JSON."""
    try:
        registry = _build_registry()
        diagnostics = registry.diagnose_all()
        engine = _get_cost_engine()

        output = {
            "providers": [
                {
                    "provider": d.provider_name,
                    "status": d.status,
                    "detected_path": d.detected_path,
                    "last_parsed": d.last_parsed,
                    "error_message": d.error_message,
                    "accuracy_confidence": d.accuracy_confidence,
                }
                for d in diagnostics
            ],
            "pricing_version": engine.get_version(),
            "pricing_stale": engine.is_stale(30),
            "has_new_events": False,  # Phase 1: always False (no event bus polling yet)
        }
        print(json.dumps(output, ensure_ascii=False))
        return 0
    except Exception as exc:
        sys.stderr.write(f"[provider_engine diagnose] Error: {exc}\n")
        return 1


# ------------------------------------------------------------------ #
#  Subcommand: reprice & usage                                         #
# ------------------------------------------------------------------ #

def cmd_reprice(args) -> int:
    """Reprice all requests that do not have locked pricing version."""
    from db import PROJECT_DB, init_db_schema
    from cost_engine import CostEngine
    from datetime import datetime
    import sqlite3

    conn = sqlite3.connect(PROJECT_DB)
    try:
        init_db_schema(conn)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT request_id, provider, model, timestamp, input_tokens, output_tokens, cache_tokens, thinking_tokens, tool_tokens
            FROM provider_requests
            WHERE pricing_version IS NULL OR pricing_version = ''
        """)
        rows = cursor.fetchall()

        engine = CostEngine(db_conn=conn)
        latest_version = engine.get_version()
        effective_date = datetime.now().strftime("%Y-%m-%d")

        # Snapshot local rates to pricing_versions db table
        pricing_data = engine._load()
        for prov_name, prov_val in pricing_data.get("providers", {}).items():
            for model_name, model_val in prov_val.get("models", {}).items():
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO pricing_versions (
                            provider, model, version, effective_date,
                            input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok,
                            thinking_per_mtok, tool_per_mtok, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prov_name, model_name, latest_version, effective_date,
                        float(model_val.get("input_per_mtok", 0)),
                        float(model_val.get("output_per_mtok", 0)),
                        float(model_val.get("cache_read_per_mtok", 0)),
                        float(model_val.get("cache_write_per_mtok", 0)),
                        float(model_val.get("thinking_per_mtok", 0)),
                        float(model_val.get("tool_per_mtok", 0)),
                        datetime.now().astimezone().isoformat()
                    ))
                except Exception:
                    pass
        conn.commit()

        updated_count = 0
        reprice_version = f"reprice-{effective_date}"

        for row in rows:
            req_id, provider, model, ts, inp, out, cache, think, tool = row
            from connectors.base import NormalizedUsageRecord
            rec = NormalizedUsageRecord(
                provider=provider,
                model=model,
                conversation_id="reprice",
                request_id=req_id,
                timestamp=ts,
                input_tokens=inp,
                output_tokens=out,
                cache_read_tokens=cache,
                cache_write_tokens=0,
                thinking_tokens=think,
                tool_tokens=tool,
            )
            cost_result = engine.calculate(rec, pricing_version=latest_version)
            engine.lock_cost(conn, req_id, cost_result, reprice_version)
            updated_count += 1

        print(json.dumps({"status": "success", "updated_count": updated_count}))
        return 0
    except Exception as e:
        sys.stderr.write(f"[provider_engine reprice] Error: {e}\n")
        return 1
    finally:
        conn.close()


def cmd_usage(args) -> int:
    """Delegate to usage_validator module."""
    from usage_validator import UsageValidator
    from db import PROJECT_DB
    import sqlite3

    conn = sqlite3.connect(PROJECT_DB)
    try:
        validator = UsageValidator(conn)
        if args.usage_subcommand == "validate":
            res = validator.validate()
            print(json.dumps(res, ensure_ascii=False))
            return 1 if res.get("status") == "violations" else 0
        elif args.usage_subcommand == "reconcile":
            res = validator.reconcile()
            print(json.dumps(res, ensure_ascii=False))
            return 0
        elif args.usage_subcommand == "doctor":
            res = validator.doctor()
            print(json.dumps(res, ensure_ascii=False))
            return 0
        elif args.usage_subcommand == "diff":
            res = validator.diff(args.run_a, args.run_b)
            if res.get("status") == "error":
                sys.stderr.write(res.get("message") + "\n")
                return 2
            print(json.dumps(res, ensure_ascii=False))
            return 0
    except Exception as e:
        sys.stderr.write(f"[provider_engine usage] Error: {e}\n")
        return 1
    finally:
        conn.close()


# ------------------------------------------------------------------ #
#  CLI entry point                                                     #
# ------------------------------------------------------------------ #

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="provider_engine",
        description="Provider-Centric Runtime & Usage Engine CLI (FEAT-048 / FEAT-049)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # detect
    detect_parser = subparsers.add_parser("detect", help="Detect installed providers")
    detect_parser.set_defaults(func=cmd_detect)

    # parse
    parse_parser = subparsers.add_parser("parse", help="Parse usage for a conversation")
    parse_parser.add_argument("--provider", required=True, help="Provider name")
    parse_parser.add_argument("--conv-id", dest="conv_id", required=True, help="Conversation ID")
    parse_parser.set_defaults(func=cmd_parse)

    # pricing
    pricing_parser = subparsers.add_parser("pricing", help="Calculate cost for token counts")
    pricing_parser.add_argument("--provider", required=True)
    pricing_parser.add_argument("--model", required=True)
    pricing_parser.add_argument("--input", type=int, default=0)
    pricing_parser.add_argument("--output", type=int, default=0)
    pricing_parser.add_argument("--cache-read", type=int, default=0, dest="cache_read")
    pricing_parser.add_argument("--cache-write", type=int, default=0, dest="cache_write")
    pricing_parser.add_argument("--thinking", type=int, default=0)
    pricing_parser.set_defaults(func=cmd_pricing)

    # diagnose
    diagnose_parser = subparsers.add_parser("diagnose", help="Run provider diagnostics")
    diagnose_parser.set_defaults(func=cmd_diagnose)

    # reprice
    reprice_parser = subparsers.add_parser("reprice", help="Reprice requests with latest pricing rules")
    reprice_parser.set_defaults(func=cmd_reprice)

    # usage
    usage_parser = subparsers.add_parser("usage", help="Usage audit subcommands")
    usage_parser.set_defaults(func=cmd_usage)
    usage_subparsers = usage_parser.add_subparsers(dest="usage_subcommand", required=True)

    usage_subparsers.add_parser("validate", help="Validate database records for value anomalies")
    usage_subparsers.add_parser("reconcile", help="Sync and reconcile transcript history")
    usage_subparsers.add_parser("doctor", help="Run diagnostic health-check and resolutions")
    
    diff_parser = usage_subparsers.add_parser("diff", help="Diff two reconciliation runs")
    diff_parser.add_argument("--run-a", type=int, required=True)
    diff_parser.add_argument("--run-b", type=int, required=True)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
