# bootstrap.py
import os
import json
from common import log_info, log_success, log_error, session_start, session_step, session_complete, session_fail
from config import load_memory_config, get_memory_paths
from scanner import ProjectScanner
from analyzer import ProjectAnalyzer
from markdown_writer import write_project_summary, write_architecture_overview
from json_writer import write_file_map, update_memory_state
from sqlite_writer import init_sqlite_indexes
from git_diff import get_latest_commit_hash

def run_bootstrap() -> dict:
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
        build_commands = scanner.detect_build_commands()
        
        info = {
            "project_name": config.get("project_id", "ai-skill-framework"),
            "description": "A reusable collection of engineering skills for AI coding agents to manage SDLC lifecycle",
            "languages": languages,
            "frameworks": frameworks,
            "modules": modules,
            "databases": databases,
            "build_commands": build_commands
        }
        
        session_step(
            step="Writing summary and indexes...",
            log_msg="> Writing project-summary.md and architecture/overview.md..."
        )
        
        # 3. Sinh Markdown tri thức
        write_project_summary(paths["summary"], info)
        write_architecture_overview(os.path.join(paths["architecture_dir"], "overview.md"), info)
        
        # 4. Sinh file-map.json
        write_file_map(os.path.join(paths["memory_root"], "indexes", "file-map.json"), scanner.files)
        
        # 5. Khởi tạo SQLite
        init_sqlite_indexes()
        
        # 6. Tạo lessons mặc định nếu chưa có
        for lesson_file in ["known-problems.md", "architectural-decisions.md"]:
            dest = os.path.join(paths["lessons_dir"], lesson_file)
            if not os.path.exists(dest):
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(f"# {lesson_file.replace('-', ' ').replace('.md', '').title()}\n\n")
                    
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
        
        return {
            "status": "success",
            "message": "Project memory bootstrapped successfully.",
            "data": {
                "languages": languages,
                "frameworks": frameworks,
                "modules_count": len(modules),
                "git_hash": git_hash
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
