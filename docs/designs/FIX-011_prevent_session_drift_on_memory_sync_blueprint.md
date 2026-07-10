<!-- File path: docs/designs/FIX-011_prevent_session_drift_on_memory_sync_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-011
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Prevent Session Drift on Memory Sync

## 1. Proposed Code Changes

### [Component: Project Memory Script Helpers]

Chỉnh sửa tệp hỗ trợ quản lý phiên làm việc [common.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/common.py) để tránh việc vô tình thay đổi thông tin điều hướng của phiên khi chạy lệnh đồng bộ bộ nhớ ngầm.

#### [MODIFY] [common.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/common.py)

Thay thế nội dung các hàm `session_start`, `session_step`, `session_complete`, và `session_fail` bằng logic mới:

- **Hàm `session_start`**:
  ```python
  def session_start(skill: str, command: str, checkpoint: int, step: str):
      if integrate_runtime_api():
          try:
              workflow_runtime = __import__("workflow_runtime")
              session_module = __import__("session")
              load_session = session_module.load_session
              save_session_atomic = session_module.save_session_atomic
              
              session = load_session()
              if not session:
                  session = {"workspace": {"path": ".", "valid": True}}
              
              # Nếu session đang chạy một skill khác (ví dụ: đang code ở checkpoint 5),
              # bỏ qua việc bắt đầu session này để tránh ghi đè tiến trình
              active_skill = session.get("current_skill")
              if active_skill and active_skill != skill:
                  log_info(f"Skipping session start for '{skill}' because active skill is '{active_skill}'.")
                  return

              session["status"] = "in_progress"  # type: ignore
              session["checkpoint"] = checkpoint  # type: ignore
              session["current_skill"] = skill  # type: ignore
              session["current_command"] = command  # type: ignore
              session["current_step"] = step  # type: ignore
              session["current_logs"] = [f"> Starting {skill}..."]  # type: ignore
              workflow_runtime.update_context_health(session)
              save_session_atomic(session)
              log_info(f"Session updated: {skill} start.")
          except Exception as e:
              log_warn(f"Failed to call runtime start API: {e}")
  ```

- **Hàm `session_step`**:
  ```python
  def session_step(step: str, log_msg: str):
      if integrate_runtime_api():
          try:
              workflow_runtime = __import__("workflow_runtime")
              session_module = __import__("session")
              load_session = session_module.load_session
              save_session_atomic = session_module.save_session_atomic
              
              session = load_session()
              if session:
                  active_skill = session.get("current_skill")
                  if active_skill and active_skill not in ["project-memory-update", "project-memory-bootstrap"]:
                      return

                  session["current_step"] = step  # type: ignore
                  if "current_logs" not in session or not isinstance(session["current_logs"], list):
                      session["current_logs"] = []  # type: ignore
                  if log_msg:
                      session["current_logs"].append(log_msg)  # type: ignore
                  workflow_runtime.update_context_health(session)
                  save_session_atomic(session)
          except Exception as e:
              log_warn(f"Failed to call runtime step API: {e}")
  ```

- **Hàm `session_complete`**:
  ```python
  def session_complete(checkpoint: int, step: str, next_skill: str, next_cmd: str):
      if integrate_runtime_api():
          try:
              workflow_runtime = __import__("workflow_runtime")
              session_module = __import__("session")
              load_session = session_module.load_session
              save_session_atomic = session_module.save_session_atomic
              
              session = load_session()
              if session:
                  active_skill = session.get("current_skill")
                  if active_skill and active_skill not in ["project-memory-update", "project-memory-bootstrap"]:
                      # Vẫn cập nhật context health để đồng bộ thông số bộ nhớ, RAG và Git mới nhất
                      workflow_runtime.update_context_health(session)
                      save_session_atomic(session)
                      log_info("Skipped workflow routing update of session, but updated context health successfully.")
                      return

                  session["status"] = "completed"  # type: ignore
                  session["checkpoint"] = checkpoint  # type: ignore
                  session["current_step"] = step  # type: ignore
                  if "current_logs" not in session or not isinstance(session["current_logs"], list):
                      session["current_logs"] = []  # type: ignore
                  session["current_logs"].append("> Completed successfully.")  # type: ignore
                  session["suggested_next_skill"] = next_skill  # type: ignore
                  session["suggested_next_command"] = next_cmd  # type: ignore
                  workflow_runtime.update_context_health(session)
                  save_session_atomic(session)
                  log_success(f"Session completed: checkpoint {checkpoint} reached.")
          except Exception as e:
              log_warn(f"Failed to call runtime complete API: {e}")
  ```

- **Hàm `session_fail`**:
  ```python
  def session_fail(step: str, log_msg: str):
      if integrate_runtime_api():
          try:
              workflow_runtime = __import__("workflow_runtime")
              session_module = __import__("session")
              load_session = session_module.load_session
              save_session_atomic = session_module.save_session_atomic
              
              session = load_session()
              if session:
                  active_skill = session.get("current_skill")
                  if active_skill and active_skill not in ["project-memory-update", "project-memory-bootstrap"]:
                      return

                  session["status"] = "failed"  # type: ignore
                  session["current_step"] = step  # type: ignore
                  if "current_logs" not in session or not isinstance(session["current_logs"], list):
                      session["current_logs"] = []  # type: ignore
                  session["current_logs"].append(f"Error: {log_msg}")  # type: ignore
                  workflow_runtime.update_context_health(session)
                  save_session_atomic(session)
          except Exception as e:
              log_warn(f"Failed to call runtime fail API: {e}")
  ```

## 2. Test Plan

### Kịch bản kiểm thử tự động
- Chạy toàn bộ bộ unit test hiện có của runtime:
  `pytest skills/workflow-runtime/tests/` hoặc `npm test` nếu có liên quan.
  *(Kiểm tra đảm bảo các thay đổi không phá vỡ logic chung).*

### Kịch bản kiểm thử thủ công
1. Thiết lập một checkpoint giả định (ví dụ: checkpoint `5`) bằng cách trực tiếp sửa `.agents/.session.json` hoặc chạy lệnh:
   `python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py start --skill "quick-fix" --command "fix" --checkpoint 5 --step "Starting execution..."`
2. Chạy lệnh cập nhật bộ nhớ:
   `python3 runtime/scripts/project_memory/cli.py update`
3. Xác nhận rằng:
   - CLI thông báo cập nhật thành công (hoặc không có file thay đổi).
   - Nội dung tệp `.agents/.session.json` **vẫn duy trì checkpoint 5**, `current_skill` vẫn là `"quick-fix"`, không bị nhảy lùi về checkpoint 2 hay kỹ năng `project-memory-update`.
   - Các trường `memory` và `rag` trong session được cập nhật trạng thái mới nhất thành công.
