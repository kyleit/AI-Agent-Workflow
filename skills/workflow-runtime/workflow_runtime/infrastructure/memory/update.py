from __future__ import annotations

import json
import os
import re
from typing import Any, cast

from .common import (log_warn, session_complete, session_fail, session_start,
                     session_step)
from .config import get_memory_paths, load_memory_config
from .filesystem import get_changed_files_by_timestamp, get_project_files
from .git_diff import (get_changed_files, get_latest_commit_hash,
                       get_uncommitted_files, is_git_repository)
from .json_writer import (generate_file_map,
                         update_memory_state)  # pyright: ignore[reportUnknownVariableType]
from .vector_manifest import \
    write_vector_sync_plan  # pyright: ignore[reportUnknownVariableType]


def parse_new_lessons(file_path: str) -> list[dict[str, Any]]:
    """Phân tích các tệp issue/quick-fix/brainstorming để trích xuất bài học hoặc lỗi đã biết."""
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    lessons: list[dict[str, Any]] = []
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


def run_update(force_full: bool = False, target_dir: str | None = None) -> dict[str, Any]:
    session_start(
        skill="project-memory-update",
        command="memory-sync",
        checkpoint=2,
        step="Starting memory update..."
    )

    try:
        root_dir = os.path.abspath(target_dir or os.getcwd())
        config = load_memory_config(root_dir=root_dir)
        paths = get_memory_paths(config, root_dir=root_dir)

        last_hash = ""
        last_updated = ""
        if os.path.exists(paths["state"]):
            try:
                with open(paths["state"], "r", encoding="utf-8") as f:
                    state = json.load(f)
                    if isinstance(state, dict):
                        state_dict = cast(dict[str, Any], state)
                        last_hash = str(state_dict.get("last_git_hash", ""))
                        last_updated = str(state_dict.get("last_updated_at", ""))
            except Exception:
                pass

        session_step(step="Detecting changes...", log_msg="> Running change detection algorithms...")
        changed_files: list[str] = []
        detection_method = "user-specified"

        if force_full:
            changed_files = get_project_files(root_dir=root_dir)
            detection_method = "full-scan"
        elif is_git_repository(root_dir):
            detection_method = "git-diff"
            if last_hash:
                changed_files = get_changed_files(last_hash, root_dir=root_dir)
            else:
                changed_files = get_project_files(root_dir=root_dir)
            changed_files = list(set(changed_files + get_uncommitted_files(root_dir=root_dir)))
        else:
            detection_method = "filesystem-timestamp"
            if last_updated:
                changed_files = get_changed_files_by_timestamp(last_updated, root_dir=root_dir)
            else:
                changed_files = get_project_files(root_dir=root_dir)

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

        session_step(step="Classifying changes...", log_msg="> Classifying modified files and mapping to layers...")

        file_map_path = os.path.join(paths["memory_root"], "indexes", "file-map.json")
        file_map: dict[str, Any] = {}
        if os.path.exists(file_map_path):
            try:
                with open(file_map_path, "r", encoding="utf-8") as f:
                    raw_fm = json.load(f)
                    if isinstance(raw_fm, dict):
                        file_map = cast(dict[str, Any], raw_fm)
            except Exception:
                pass
        if not file_map:
            file_map = generate_file_map(get_project_files(root_dir=root_dir))

        new_lessons: list[dict[str, Any]] = []
        for file in changed_files:
            if (
                file.startswith("docs/issues/")
                or file.startswith("docs/quick/")
                or file.startswith("docs/features/")
            ):
                full_path = os.path.join(root_dir, file)
                new_lessons.extend(parse_new_lessons(full_path))

        lessons_updated = 0
        upsert_chunks: list[dict[str, Any]] = []
        files_written: list[str] = []

        if new_lessons and os.path.exists(paths["known_problems"]):
            try:
                with open(paths["known_problems"], "r", encoding="utf-8") as f:
                    current_content = f.read()

                append_content = ""
                for l in new_lessons:
                    l_id = str(l.get("id", ""))
                    l_title = str(l.get("title", ""))
                    l_prob = str(l.get("problem", ""))
                    l_fix = str(l.get("fix", ""))

                    if l_id.upper() not in current_content.upper():
                        append_content += f"\n## {l_title}\n"
                        append_content += f"- **Problem**: {l_prob}\n"
                        append_content += f"- **Fix**: {l_fix}\n"

                        upsert_chunks.append({
                            "id": l_id,
                            "text": f"{l_title}: Problem: {l_prob} Fix: {l_fix}",
                            "metadata": {
                                "type": "lessons",
                                "tags": ["known-problems", "bug-fix"]
                            }
                        })

                if append_content:
                    with open(paths["known_problems"], "a", encoding="utf-8") as f:
                        f.write(append_content)
                    lessons_updated += 1
                    files_written.append(paths["known_problems"])
            except Exception as e:
                log_warn(f"Failed to update known-problems.md: {e}")

        if upsert_chunks:
            proj_id = str(config.get("project_id", os.path.basename(root_dir) if os.path.basename(root_dir) else "unknown_project"))
            write_vector_sync_plan(
                paths["vector_sync_plan"],
                proj_id,
                cast(Any, upsert_chunks)
            )
            files_written.append(paths["vector_sync_plan"])

        current_hash = get_latest_commit_hash(root_dir=root_dir)
        update_memory_state(paths["state"], cast(Any, {
            "last_git_hash": current_hash or last_hash,
            "last_run_mode": "incremental",
            "files_changed": len(changed_files),
            "memory_docs_updated": lessons_updated,
            "layers_generated": ["lessons", "rag"]
        }))
        files_written.append(paths["state"])

        session_complete(
            checkpoint=2,
            step="Step Complete",
            next_skill="brainstorming",
            next_cmd="brainstorm"
        )

        return {
            "status": "success",
            "message": "Project memory updated successfully.",
            "files_read": changed_files,
            "files_written": files_written,
            "data": {
                "detection_method": detection_method,
                "files_changed_count": len(changed_files),
                "changed_files": changed_files[:10],
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
