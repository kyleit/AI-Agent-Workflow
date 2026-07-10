<!-- File path: docs/plans/FEAT-018_multi_agent_orchestration_plan.md -->

---
feature_id: FEAT-018
feature_name: Multi-Agent Orchestration Framework
status: reviewed
stage: planning
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: ../brainstorming/FEAT-018_multi_agent_orchestration.md
next_artifact: ../designs/FEAT-018_multi_agent_orchestration_blueprint.md
---

# FEAT-018: Multi-Agent Orchestration Framework

## Objective
- Thiết lập một tầng trí tuệ cấp cao làm điểm đầu vào duy nhất cho toàn bộ hệ thống (`/orchestrate`).
- Tự động hóa việc phân tích ý định, lựa chọn kỹ năng, chia tác vụ song song, kiểm soát khóa tệp, và hợp nhất kết quả một cách an toàn mà vẫn giữ nguyên tính tương thích ngược cho hệ thống hiện tại.

## Scope

### Included
- Tạo kỹ năng mới [skills/orchestrator/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/orchestrator/SKILL.md).
- Mở rộng công cụ CLI `workflow_runtime.py` hỗ trợ các tác vụ: lập lịch DAG, quản lý khóa tệp `file-locks.json`, kiểm tra xung đột ghi tệp, và hợp nhất các thay đổi.
- Cập nhật chính sách toàn cục trong `AI_RULES.md` thêm phần **Multi-Agent Orchestration Policy**.
- Điều chỉnh các kỹ năng hiện tại để đóng vai trò "worker" tuân thủ cơ chế khóa tệp và không tự ý phân phối agent.
- Cập nhật tài liệu dự án (`MANIFEST.json`, `README.md`, `USAGE.md`).

### Excluded
- Không xóa bỏ hoặc thay đổi cơ chế gọi trực tiếp các kỹ năng cũ (để giữ tương thích ngược).
- Không tự động hóa hoàn toàn các cổng phê duyệt Git (như push, tag, commit) ngoại trừ trong chế độ `unrestricted`.

## Project Impact
- **Tác động rất lớn**:
  - `skills/workflow-runtime/` (Logic cốt lõi để lập lịch song song và khóa tệp).
  - `AI_RULES.md` (Chính sách phân quyền Multi-Agent mới).
  - Toàn bộ 24 kỹ năng hiện tại (Chuyển đổi vai trò sang worker tuân thủ cơ chế locking).

## Dependencies
- Phụ thuộc vào công cụ `workflow_runtime.py` hiện tại của hệ thống.
- Cần có Python để thực thi các tiến trình song song.

## Risks
- **Trùng lặp ghi tệp khi chạy song song**: Agent A và Agent B cùng sửa đổi một tệp dẫn đến mất mát mã nguồn.
  - *Giảm thiểu*: Sử dụng cơ chế khóa tệp nghiêm ngặt tại `file-locks.json` được kiểm tra trước khi cấp quyền chạy tác vụ.
- **Tiêu tốn Token cao**: Khi chạy nhiều agent song song, lượng token tiêu hao có thể tăng vọt.
  - *Giảm thiểu*: Thiết lập cổng phê duyệt của người dùng trước khi tiến hành chạy song song, kèm theo ước tính chi phí.

## Acceptance Criteria
- Người dùng chỉ cần gọi `/orchestrate <yêu cầu>` để thực thi toàn bộ luồng công việc.
- Hệ thống tự động biên dịch sơ đồ DAG và chạy song song các tiến trình độc lập.
- Xung đột tệp được phát hiện và cảnh báo trước khi thực hiện.
- Tính tương thích ngược được đảm bảo (chạy trực tiếp các kỹ năng cũ vẫn hoạt động bình thường).

## Deliverables
- Tệp cấu hình kỹ năng mới `skills/orchestrator/SKILL.md`.
- Các bản cập nhật trong kịch bản `workflow-runtime` và `AI_RULES.md`.
- Các bản nâng cấp cấu trúc tệp của các kỹ năng worker hiện tại.

## Estimated Complexity
- **High**: Việc quản lý tiến trình song song trong môi trường Python CLI, đồng bộ hóa khóa tệp liên kết với giao thức Agent, và hợp nhất mã nguồn đòi hỏi kiểm soát logic cực kỳ chuẩn xác để tránh xung đột mã nguồn.

## Recommended Next Skill
/blueprint
