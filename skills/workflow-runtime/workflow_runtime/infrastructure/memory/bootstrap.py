# bootstrap.py
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .ai_synthesizer import AISynthesizer
from .analyzer import ProjectAnalyzer
from .common import session_complete, session_fail, session_start, session_step
from .config import get_memory_paths, load_memory_config
from .context_manifest import build_project_context_manifest, write_context_manifest
from .context_extractor import ProjectContextExtractor
from .git_diff import get_latest_commit_hash
from .json_writer import (generate_file_map, update_memory_state,
                          write_file_map)
from .markdown_writer import (write_architecture_api_contracts,
                              write_architecture_components,
                              write_architecture_data_flows,
                              write_architecture_dependencies,
                              write_architecture_domain_models,
                              write_architecture_overview, write_database_catalog,
                              write_dependency_catalog, write_endpoint_catalog,
                              write_entrypoint_catalog, write_module_catalog,
                              write_source_catalog,
                              write_lessons_learned, write_project_summary)
from .scanner import ProjectScanner
from .sqlite_writer import populate_indexed_files
from .common import write_json_safe


def run_bootstrap(target_dir: str | None = None, enable_ai: bool = False) -> dict[str, Any]:
    session_start(
        skill="project-memory-bootstrap",
        command="memory-init",
        checkpoint=1,
        step="Starting deep memory bootstrapping"
    )

    try:
        config = load_memory_config(root_dir=target_dir)
        paths = get_memory_paths(config, root_dir=target_dir)

        # 1. Tao cac thu muc dich
        os.makedirs(paths["memory_root"], exist_ok=True)
        os.makedirs(paths["architecture_dir"], exist_ok=True)
        os.makedirs(paths["lessons_dir"], exist_ok=True)
        os.makedirs(paths["rag_dir"], exist_ok=True)

        session_step(
            step="Scanning workspace",
            log_msg="> Scanning workspace with strict ignore filters"
        )

        # 2. Quet du an (AST + Filesystem)
        scanner = ProjectScanner(root_dir=target_dir)
        analyzer = ProjectAnalyzer(root_dir=target_dir)
        extractor = ProjectContextExtractor(root_dir=target_dir)

        root = os.path.abspath(target_dir or os.getcwd())
        languages = scanner.detect_languages()
        frameworks = scanner.detect_frameworks(languages)
        source_records = scanner.source_catalog(revision=get_latest_commit_hash(root_dir=target_dir) or "WORKTREE")
        dependencies = analyzer.analyze_dependencies()
        endpoints = analyzer.analyze_endpoints()
        entrypoint_records = extractor.extract_entrypoint_records()
        modules = analyzer.analyze_module_catalog(extractor.extract_code_symbols(), dependencies)
        databases = analyzer.get_database_info()
        database_records = analyzer.analyze_database_catalog()
        infrastructure = analyzer.detect_infrastructure()
        build_commands = scanner.detect_build_commands()
        symbols = extractor.extract_code_symbols()

        proj_name = config.get("project_id") or (os.path.basename(os.path.abspath(target_dir)) if target_dir else "ai-skill-framework")
        info = {
            "project_name": proj_name,
            "description": f"A software project for {proj_name}.",
            "languages": languages,
            "frameworks": frameworks,
            "modules": modules,
            "databases": databases,
            "database_records": database_records,
            "dependencies": dependencies,
            "endpoints": endpoints,
            "entrypoints": entrypoint_records,
            "source_records": source_records,
            "symbols": symbols,
            "infrastructure": infrastructure,
            "build_commands": build_commands
        }

        # 3. AI Cognitive Synthesis (neu duoc bat)
        ai_synth_data: dict[str, Any] | None = None
        if enable_ai:
            session_step(
                step="AI Cognitive Synthesis",
                log_msg="> Performing deep AI cognitive architecture analysis"
            )
            synthesizer = AISynthesizer(root_dir=target_dir)
            ai_synth_data = synthesizer.synthesize()

        session_step(
            step="Writing deep memory layers",
            log_msg="> Generating project-summary and complete architecture suite"
        )

        files_written: list[str] = []

        # 4. Sinh Project Summary & Architecture Suite voi AI synthesis
        write_project_summary(paths["summary"], info, ai_synth_data)
        files_written.append(paths["summary"])

        arch_overview = os.path.join(paths["architecture_dir"], "overview.md")
        write_architecture_overview(arch_overview, info, ai_synth_data)
        files_written.append(arch_overview)

        arch_components = os.path.join(paths["architecture_dir"], "components.md")
        write_architecture_components(arch_components, info, ai_synth_data)
        files_written.append(arch_components)

        arch_flows = os.path.join(paths["architecture_dir"], "data-flows.md")
        write_architecture_data_flows(arch_flows, ai_synth_data)
        files_written.append(arch_flows)

        arch_apis = os.path.join(paths["architecture_dir"], "api-contracts.md")
        write_architecture_api_contracts(arch_apis, info, ai_synth_data)
        files_written.append(arch_apis)

        arch_models = os.path.join(paths["architecture_dir"], "domain-models.md")
        write_architecture_domain_models(arch_models, symbols)
        files_written.append(arch_models)

        arch_deps = os.path.join(paths["architecture_dir"], "dependencies.md")
        write_architecture_dependencies(arch_deps, info)
        files_written.append(arch_deps)

        catalog_documents = {
            "source_inventory": os.path.join(paths["architecture_dir"], "source-inventory.md"),
            "modules": os.path.join(paths["architecture_dir"], "modules.md"),
            "entrypoints": os.path.join(paths["architecture_dir"], "entrypoints.md"),
            "endpoints": os.path.join(paths["architecture_dir"], "endpoints.md"),
            "databases": os.path.join(paths["architecture_dir"], "databases.md"),
            "dependencies": os.path.join(paths["architecture_dir"], "dependency-catalog.md"),
            "catalogs_json": os.path.join(paths["architecture_dir"], "catalogs.json"),
        }
        write_source_catalog(catalog_documents["source_inventory"], source_records)
        write_module_catalog(catalog_documents["modules"], modules)
        write_entrypoint_catalog(catalog_documents["entrypoints"], entrypoint_records)
        write_endpoint_catalog(catalog_documents["endpoints"], endpoints)
        write_database_catalog(catalog_documents["databases"], database_records)
        write_dependency_catalog(catalog_documents["dependencies"], dependencies)
        write_json_safe(catalog_documents["catalogs_json"], {
            "source_records": source_records,
            "module_records": modules,
            "entrypoint_records": entrypoint_records,
            "endpoint_records": endpoints,
            "database_records": database_records,
            "dependency_records": dependencies,
            "symbol_records": symbols,
        })
        files_written.extend(catalog_documents.values())

        # 5. Sinh Lessons Learned
        write_lessons_learned(paths["lessons_dir"], ai_synth_data)
        files_written.append(os.path.join(paths["lessons_dir"], "architectural-decisions.md"))
        files_written.append(os.path.join(paths["lessons_dir"], "known-problems.md"))

        # 6. Sinh file-map.json va SQLite Index
        file_map = os.path.join(paths["memory_root"], "indexes", "file-map.json")
        file_map_data = generate_file_map(scanner.files)
        write_file_map(file_map, scanner.files)
        files_written.append(file_map)

        populate_indexed_files(file_map_data, os.path.join(root, ".agents", "project_runtime.db"))

        # 7. Cap nhat memory-state.json
        git_hash = get_latest_commit_hash(root_dir=target_dir)
        update_memory_state(paths["state"], {
            "last_git_hash": git_hash,
            "memory_version": "2.1.0",
            "last_run_mode": "ai_cognitive" if ai_synth_data else "heuristic",
            "files_changed": 0,
            "total_files_indexed": len(scanner.files),
            "catalog_counts": {
                "source_records": len(source_records),
                "module_records": len(modules),
                "entrypoint_records": len(entrypoint_records),
                "endpoint_records": len(endpoints),
                "database_records": len(database_records),
                "dependency_records": len(dependencies),
                "symbol_records": len(symbols),
            },
            "inventory_revision": source_records[0].get("revision", "WORKTREE") if source_records else "WORKTREE",
            "memory_docs_updated": len(files_written),
            "ai_synthesis_enabled": bool(ai_synth_data),
            "layers_generated": [
                "summary", "overview", "components", "data-flows",
                "api-contracts", "domain-models", "dependencies", "lessons", "indexes"
            ]
        })
        files_written.append(paths["state"])

        manifest = build_project_context_manifest(
            root=Path(root),
            project_id=str(proj_name),
            summary_path=os.path.relpath(paths["summary"], target_dir or os.getcwd()).replace("\\", "/"),
            architecture_paths=[
                os.path.relpath(path, target_dir or os.getcwd()).replace("\\", "/")
                for path in [arch_overview, arch_components, arch_flows, arch_apis, arch_models, arch_deps]
            ],
            entrypoints=[str(item["path"]) for item in entrypoint_records],
            active_constraints=["AI_RULES.md", "AGENTS.md", "no blueprint no code"],
            known_blockers=[],
            index_revision=git_hash,
            retrieval_hints=["workflow runtime", "project architecture", "active gates"],
            generated_at=datetime.now().astimezone().isoformat(),
            catalog_paths=[
                os.path.relpath(path, root).replace("\\", "/")
                for path in catalog_documents.values()
            ],
            catalog_counts={
                "source_records": len(source_records),
                "module_records": len(modules),
                "entrypoint_records": len(entrypoint_records),
                "endpoint_records": len(endpoints),
                "database_records": len(database_records),
                "dependency_records": len(dependencies),
                "symbol_records": len(symbols),
            },
        )
        write_context_manifest(paths["context_manifest"], manifest)
        files_written.append(paths["context_manifest"])

        session_complete(
            checkpoint=2,
            step="Memory Bootstrapping Complete",
            next_skill="brainstorming",
            next_cmd="brainstorm"
        )

        return {
            "status": "success",
            "command": "memory bootstrap",
            "summary": f"Deep cognitive memory generated successfully ({len(files_written)} documents, {len(scanner.files)} files indexed, AI synthesis: {bool(ai_synth_data)}).",
            "files_read": scanner.files,
            "files_written": files_written,
            "next_skill": "brainstorming"
        }

    except Exception as e:
        session_fail(
            step="Memory Bootstrapping Failed",
            log_msg=f"Error during deep memory bootstrapping: {str(e)}"
        )
        return {
            "status": "failure",
            "command": "memory bootstrap",
            "summary": f"Error: {str(e)}",
            "warnings": [str(e)],
            "files_read": [],
            "files_written": [],
            "next_skill": None
        }


__all__ = ["run_bootstrap"]
