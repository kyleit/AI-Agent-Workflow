from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from typing import Any, cast

from .common import log_info, log_warn
from .context_extractor import ProjectContextExtractor


class AISynthesizer:
    """AI-powered cognitive synthesizer with multi-provider fallback for deep memory synthesis."""

    def __init__(self, root_dir: str | None = None) -> None:
        self.root_dir = root_dir or os.getcwd()
        self.extractor = ProjectContextExtractor(self.root_dir)

    def build_synthesis_prompt(self, context: dict[str, Any]) -> str:
        prompt = (
            "You are an expert Principal Software Architect. Analyze the following codebase context and produce a comprehensive, dense architecture intelligence report.\n\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "business_purpose": "Detailed description of the business problem, key capabilities, and value flow.",\n'
            '  "architecture_style": "Precise architecture pattern with rationale (e.g. Hexagonal, DDD, Event-Driven, Multi-Agent).",\n'
            '  "system_context": "High-level system context explaining interactions between users, clients, external APIs, and internal core.",\n'
            '  "core_subsystems": [\n'
            '    {"name": "Subsystem Name", "path": "dir_path", "purpose": "Detailed semantic role, key responsibilities, internal services."}\n'
            '  ],\n'
            '  "data_flow_description": "Step-by-step description of how requests/data flow through the system.",\n'
            '  "api_contracts_summary": "Summary of public interfaces, CLI commands, HTTP/IPC routes, or schema definitions.",\n'
            '  "invariants_and_rules": ["Key architectural invariant or safety rule."],\n'
            '  "known_pitfalls": ["Known pitfall, anti-pattern, or design constraint."]\n'
            "}\n\n"
            f"Codebase Context:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n"
        )
        return prompt

    def _synthesize_via_agy(self, prompt: str) -> dict[str, Any] | None:
        if shutil.which("agy"):
            prompt_file = os.path.join(self.root_dir, ".agents", "memory", "synthesis_prompt.json")
            try:
                with open(prompt_file, "w", encoding="utf-8") as f:
                    f.write(prompt)

                log_info("Executing cognitive synthesis via AGY AI CLI")
                cmd = ["agy", "--print", f"Analyze and synthesize architecture based on {prompt_file}"]
                res = subprocess.run(
                    cmd, cwd=self.root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=90, encoding="utf-8"
                )
                if res.returncode == 0 and res.stdout.strip():
                    raw_out = res.stdout.strip()
                    if "```json" in raw_out:
                        raw_out = raw_out.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_out:
                        raw_out = raw_out.split("```")[1].split("```")[0].strip()
                    parsed = json.loads(raw_out)
                    if isinstance(parsed, dict) and "business_purpose" in parsed:
                        return cast(dict[str, Any], parsed)
            except Exception as e:
                log_warn(f"AGY cognitive synthesis skipped: {e}")
            finally:
                if os.path.exists(prompt_file):
                    try:
                        os.remove(prompt_file)
                    except Exception:
                        pass
        return None

    def _synthesize_via_ollama(self, prompt: str) -> dict[str, Any] | None:
        try:
            req_data = json.dumps({
                "model": "qwen2.5-coder:7b",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=req_data,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_response = data.get("response", "")
                parsed = json.loads(raw_response)
                if isinstance(parsed, dict) and "business_purpose" in parsed:
                    return cast(dict[str, Any], parsed)
        except Exception:
            pass
        return None

    def _synthesize_semantic_heuristics(self, context: dict[str, Any]) -> dict[str, Any]:
        proj_name = str(context.get("project_id", "Software Project"))
        readmes = context.get("readme_docs", {})
        symbols = context.get("symbols", [])

        first_readme = list(readmes.values())[0] if readmes else ""
        purpose_line = ""
        for line in first_readme.splitlines()[:25]:
            clean = line.strip().lstrip("#").strip()
            if len(clean) > 25 and not clean.startswith(("[", "!", "<")):
                purpose_line = clean
                break

        if not purpose_line:
            purpose_line = f"{proj_name} is a software system providing core execution pipelines, domain logic, and service orchestration."

        struct_names = [s.get("name", "") for s in symbols if s.get("kind") in ("struct", "class", "interface")]
        models_str = ", ".join(struct_names[:8]) if struct_names else "Core domain models and state entities"

        return {
            "business_purpose": purpose_line,
            "architecture_style": "Clean Modular Architecture with Decoupled Presentation and Domain Layers",
            "system_context": f"{proj_name} coordinates client/user interactions across presentation adapters, domain use-cases, and persistent storage backends.",
            "core_subsystems": [],
            "data_flow_description": f"User/Client Request -> API Gateway / Presentation Router -> Domain Use-Case Pipeline ({models_str}) -> Persistent Storage / Response Adapter.",
            "api_contracts_summary": "Strongly-typed public API contracts, CLI subcommand matrix, and structured data schemas.",
            "invariants_and_rules": [
                "Strict boundary isolation between presentation controllers and internal domain models",
                "Atomic transaction logging with idempotent rollback capabilities"
            ],
            "known_pitfalls": [
                "Avoid mutating state outside designated persistence adapters",
                "Ensure proper cancellation handling for asynchronous worker routines"
            ]
        }

    def synthesize(self) -> dict[str, Any]:
        context = self.extractor.get_full_context_payload()
        prompt = self.build_synthesis_prompt(context)

        synth = self._synthesize_via_agy(prompt)
        if synth:
            return synth

        synth = self._synthesize_via_ollama(prompt)
        if synth:
            return synth

        return self._synthesize_semantic_heuristics(context)


__all__ = ["AISynthesizer"]
