# update.py
import os
import json
import re
from datetime import datetime
from common import log_info, log_success, log_warn, session_start, session_step, session_complete, session_fail, to_posix_path
from config import load_memory_config, get_memory_paths
from git_diff import get_changed_files, get_uncommitted_files, get_latest_commit_hash, is_git_repository
from filesystem import get_changed_files_by_timestamp, get_project_files
from json_writer import generate_file_map, update_memory_state
from vector_manifest import chunk_markdown_file, write_vector_sync_plan

def parse_new_lessons(file_path: str) -> list[dict]:
    """Phân tích các tệp issue/quick-fix/brainstorming để trích xuất bài học hoặc lỗi đã biết."""
    if not os.path.exists(file_path):
        return []
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []
        
    lessons = []
    # Quy tắc phân tích cơ bản cho FIX tệp tin (docs/issues/FIX-XXX)
    if "issue_id:" in content or "FIX-" in file_path:
        issue_id_match = re.search(r"issue_id:\s*(FIX-\d+)", content)
        issue_id = issue_id_match.group(1) if issue_id_match else "FIX-XXX"
        
        title_match = re.search(r"#\s+(?:Fix Document\s+–\s+)?(.*)", content)
        title = title_match.group(1).strip() if title_match else "Sửa lỗi hệ thống"
        
        problem_match = re.search(r"## 1\. Issue\s*\n(.*?)\n##", content, re.DOTALL)
        if not problem_match:
            problem_match = re.search(r"## 2\. Symptoms\s*\n(.*?)\n##", content, re.DOTALL)
            
        problem = problem_match.group(1).strip() if problem_match else "Gặp lỗi hoạt động."
        
        fix_match = re.search(r"## 3\. Root Cause\s*\n(.*?)\n##", content, re.DOTALL)
        if not fix_match:
            fix_match = re.search(r"## 6\. Proposed Changes\s*\n(.*?)\n##", content, re.DOTALL)
            
        fix_detail = fix_match.group(1).strip() if fix_match else "Đã thực hiện vá lỗi."
        
        lessons.append({
            "type": "known-problems",
            "id": f"known-problems-{issue_id.lower()}",
            "title": f"{title} ({issue_id})",
            "problem": problem,
            "fix": fix_detail
        })
        
    # Phân tích nhanh cho QUICK tệp tin (docs/quick/QUICK-XXX)
    elif "feature_id:" in content or "QUICK-" in file_path:
        feat_id_match = re.search(r"feature_id:\s*(QUICK-\d+)", content)
        feat_id = feat_id_match.group(1) if feat_id_match else "QUICK-XXX"
        
        title_match = re.search(r"#\s+(?:Mini Feature Specification\s+–\s+)?(.*)", content)
        title = title_match.group(1).strip() if title_match else "Cập nhật nhanh"
        
        problem_match = re.search(r"## 1\. Feature Goal\s*\n(.*?)\n##", content, re.DOTALL)
        problem = problem_match.group(1).strip() if problem_match else "Cập nhật yêu cầu hệ thống."
        
        fix_match = re.search(r"## 6\. Proposed Changes\s*\n(.*?)\n##", content, re.DOTALL)
        fix_detail = fix_match.group(1).strip() if fix_match else "Đã triển khai cập nhật."
        
        lessons.append({
            "type": "known-problems",
            "id": f"known-problems-{feat_id.lower()}",
            "title": f"{title} ({feat_id})",
            "problem": problem,
            "fix": fix_detail
        })
        
    return lessons

def run_update(force_full: bool = False) -> dict:
    session_start(
        skill="project-memory-update",
        command="memory-sync",
        checkpoint=2,
        step="Starting memory update..."
    )
    
    try:
        config = load_memory_config()
        paths = get_memory_paths(config)
        
        # 1. Đọc memory state cũ
        last_hash = ""
        last_updated = ""
        if os.path.exists(paths["state"]):
            try:
                with open(paths["state"], "r", encoding="utf-8") as f:
                    state = json.load(f)
                    last_hash = state.get("last_git_hash", "")
                    last_updated = state.get("last_updated_at", "")
            except Exception:
                pass
                
        # 2. Phát hiện thay đổi
        session_step(step="Detecting changes...", log_msg="> Running change detection algorithms...")
        changed_files = []
        detection_method = "user-specified"
        
        if force_full:
            changed_files = get_project_files()
            detection_method = "full-scan"
        elif is_git_repository():
            detection_method = "git-diff"
            if last_hash:
                changed_files = get_changed_files(last_hash)
            else:
                changed_files = get_project_files()
            # Thêm cả các file chưa commit
            changed_files = list(set(changed_files + get_uncommitted_files()))
        else:
            detection_method = "filesystem-timestamp"
            if last_updated:
                changed_files = get_changed_files_by_timestamp(last_updated)
            else:
                changed_files = get_project_files()
                
        if not changed_files:
            session_complete(
                checkpoint=2,
                step="Step Complete",
                next_skill="brainstorming",
                next_cmd="brainstorm"
            )
            return {
                "status": "success",
                "message": "No changes detected. Memory is already up-to-date.",
                "data": {"files_changed": 0}
            }
            
        # 3. Phân loại thay đổi & ánh xạ tệp tin
        session_step(step="Classifying changes...", log_msg="> Classifying modified files and mapping to layers...")
        
        # Nạp hoặc sinh file-map.json
        file_map_path = os.path.join(paths["memory_root"], "indexes", "file-map.json")
        file_map = {}
        if os.path.exists(file_map_path):
            try:
                with open(file_map_path, "r", encoding="utf-8") as f:
                    file_map = json.load(f)
            except Exception:
                pass
        if not file_map:
            file_map = generate_file_map(get_project_files())
            
        # 4. Trích xuất bài học mới từ các file issue/quick
        new_lessons = []
        for file in changed_files:
            if file.startswith("docs/issues/") or file.startswith("docs/quick/"):
                full_path = os.path.join(os.getcwd(), file)
                new_lessons.extend(parse_new_lessons(full_path))
                
        # 5. Cập nhật tệp known-problems.md
        lessons_updated = 0
        upsert_chunks = []
        
        if new_lessons and os.path.exists(paths["known_problems"]):
            try:
                with open(paths["known_problems"], "r", encoding="utf-8") as f:
                    current_content = f.read()
                    
                append_content = ""
                for l in new_lessons:
                    # Kiểm tra xem ID bài học đã tồn tại chưa để tránh trùng lặp
                    if l["id"].upper() not in current_content.upper():
                        append_content += f"\n## {l['title']}\n"
                        append_content += f"- **Problem**: {l['problem']}\n"
                        append_content += f"- **Fix**: {l['fix']}\n"
                        
                        # Chuẩn bị cho vector sync plan
                        upsert_chunks.append({
                            "id": l["id"],
                            "text": f"{l['title']}: Problem: {l['problem']} Fix: {l['fix']}",
                            "metadata": {
                                "type": "lessons",
                                "tags": ["known-problems", "bug-fix"]
                            }
                        })
                        
                if append_content:
                    with open(paths["known_problems"], "a", encoding="utf-8") as f:
                        f.write(append_content)
                    lessons_updated += 1
            except Exception as e:
                log_warn(f"Failed to update known-problems.md: {e}")
                
        # 6. Sinh vector-sync-plan.json
        if upsert_chunks:
            write_vector_sync_plan(
                paths["vector_sync_plan"],
                config.get("vector_collection", "ai-skill-framework"),
                upsert_chunks
            )
            
        # 7. Cập nhật memory-state.json
        current_hash = get_latest_commit_hash()
        update_memory_state(paths["state"], {
            "last_git_hash": current_hash or last_hash,
            "last_run_mode": "incremental",
            "files_changed": len(changed_files),
            "memory_docs_updated": lessons_updated,
            "layers_generated": ["lessons", "rag"]
        })
        
        # 8. Tự động đồng bộ sang Obsidian qua knowledge-runtime
        try:
            try:
                import knowledge_runtime
            except ImportError:
                import sys
                framework_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                kr_scripts = os.path.join(framework_root, "skills", "knowledge-runtime", "scripts")
                if kr_scripts not in sys.path:
                    sys.path.append(kr_scripts)
                import knowledge_runtime
            
            # Kích hoạt đồng bộ Obsidian
            sync_res = knowledge_runtime.sync("obsidian")
            if sync_res.get("status") == "success":
                log_success("Obsidian sync completed automatically after memory update.")
            else:
                log_warn(f"Obsidian auto-sync returned status: {sync_res.get('message')}")
        except Exception as e:
            log_warn(f"Auto-sync Obsidian skipped: {e}")
            
        session_complete(
            checkpoint=2,
            step="Step Complete",
            next_skill="brainstorming",
            next_cmd="brainstorm"
        )
        
        return {
            "status": "success",
            "message": "Project memory updated successfully.",
            "data": {
                "detection_method": detection_method,
                "files_changed_count": len(changed_files),
                "changed_files": changed_files[:10],  # Show preview
                "lessons_appended": len(new_lessons)
            }
        }
        
    except Exception as e:
        session_fail(
            step="Update Failed",
            log_msg=str(e)
        )
        return {
            "status": "failure",
            "message": f"Failed to update project memory: {e}"
        }

if __name__ == "__main__":
    res = run_update()
    print(json.dumps(res, indent=2))
