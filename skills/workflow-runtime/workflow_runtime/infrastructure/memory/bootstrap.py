# bootstrap.py
import json
import os
from typing import Any

from .analyzer import ProjectAnalyzer
from .common import session_complete, session_fail, session_start, session_step
from .config import get_memory_paths, load_memory_config
from .git_diff import get_latest_commit_hash
from .json_writer import (generate_file_map, update_memory_state,
                          write_file_map)
from .markdown_writer import write_architecture_overview, write_project_summary
from .scanner import ProjectScanner
from .sqlite_writer import init_sqlite_indexes, populate_indexed_files


def run_bootstrap() -> dict[str, Any]:
    session_start(
        skill="project-memory-bootstrap",
        command="memory-init",
        checkpoint=1,
        step="Starting memory bootstrapping..."
    )

    try:
        config = load_memory_config()
        paths = get_memory_paths(config)

        # 1. Tạo các thư mục đích
        os.makedirs(paths["memory_root"], exist_ok=True)
        os.makedirs(paths["architecture_dir"], exist_ok=True)
        os.makedirs(paths["lessons_dir"], exist_ok=True)
        os.makedirs(paths["rag_dir"], exist_ok=True)

        session_step(
            step="Scanning workspace...",
            log_msg="> Scanning workspace and analyzing files..."
        )

        # 2. Quét dự án
        scanner = ProjectScanner()
        analyzer = ProjectAnalyzer()

        languages = scanner.detect_languages()
        frameworks = scanner.detect_frameworks(languages)
        modules = analyzer.analyze_modules()
        databases = analyzer.get_database_info()
        infrastructure = analyzer.detect_infrastructure()
        build_commands = scanner.detect_build_commands()

        info = {
            "project_name": config.get("project_id", "ai-skill-framework"),
            "description": "A reusable collection of engineering skills for AI coding agents to manage SDLC lifecycle",
            "languages": languages,
            "frameworks": frameworks,
            "modules": modules,
            "databases": databases,
            "infrastructure": infrastructure,
            "build_commands": build_commands
        }

        session_step(
            step="Writing summary and indexes...",
            log_msg="> Writing project-summary.md and architecture/overview.md..."
        )

        # 3. Sinh Markdown tri thức
        write_project_summary(paths["summary"], info)
        files_written = [paths["summary"]]

        arch_overview = os.path.join(paths["architecture_dir"], "overview.md")
        write_architecture_overview(arch_overview, info)
        files_written.append(arch_overview)

        # 4. Sinh file-map.json
        file_map = os.path.join(paths["memory_root"], "indexes", "file-map.json")
        file_map_data = generate_file_map(scanner.files)
        write_file_map(file_map, scanner.files)
        files_written.append(file_map)

        # 5. Khởi tạo và ghi chỉ mục SQLite
        populate_indexed_files(file_map_data)

        # 6. Tạo lessons mặc định nếu chưa có
        for lesson_file in ["known-problems.md", "architectural-decisions.md"]:
            dest = os.path.join(paths["lessons_dir"], lesson_file)
            if not os.path.exists(dest):
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(f"# {lesson_file.replace('-', ' ').replace('.md', '').title()}\n\n")
                files_written.append(dest)

        # 7. Cập nhật memory-state.json
        git_hash = get_latest_commit_hash()
        update_memory_state(paths["state"], {
            "last_git_hash": git_hash,
            "memory_version": "1.0.0",
            "last_run_mode": "full",
            "files_changed": 0,
            "memory_docs_updated": 2,
            "layers_generated": ["summary", "architecture", "lessons", "indexes"]
        })

        session_complete(
            checkpoint=1,
            step="Initialization Complete",
            next_skill="software-development-workflow",
            next_cmd="workflow"
        )

        files_written.append(paths["state"])

        return {
            "status": "success",
            "message": "Project memory bootstrapped successfully.",
            "files_read": scanner.files,
            "files_written": files_written,
            "data": {
                "languages": languages,
                "frameworks": frameworks,
                "modules_count": len(modules),
                "git_hash": git_hash,
                "files_scanned_count": len(scanner.files),
            }
        }

    except Exception as e:
        session_fail(
            step="Bootstrap Failed",
            log_msg=str(e)
        )
        return {
            "status": "failure",
            "message": f"Failed to bootstrap project memory: {e}"
        }

if __name__ == "__main__":
    res = run_bootstrap()
    print(json.dumps(res, indent=2))
