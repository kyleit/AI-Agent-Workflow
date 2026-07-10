<!-- File path: docs/adr/ADR-004_pure_split_state_management.md -->

# ADR-004: Pure Split State Management

## Status
Accepted

## Related Feature
[FEAT-028](file:///e:/AgentsProject/docs/brainstorming/FEAT-028_pure_split_state_management.md)

## Context
Trước đây, hệ thống AI Workflow sử dụng tệp duy nhất `.agents/.session.json` để quản lý toàn bộ trạng thái phiên (session state). Khi số lượng agents chạy song song tăng lên và các tính năng mở rộng (như phân tích token, quản lý phê duyệt) được đưa vào, tệp `.session.json` ngày càng phình to, dẫn đến các vấn đề nghiêm trọng:
1. **Xung đột Git**: Nhiều tiến trình sửa đổi một tệp lớn gây ra xung đột merge thường xuyên.
2. **Hiệu năng đĩa (I/O)**: Mỗi thao tác cập nhật nhỏ đều buộc ghi đè toàn bộ tệp lớn, làm tăng đáng kể input token cho Agent trong các lượt hội thoại tiếp theo.
3. **Tranh chấp khóa (Lock Contention)**: Các agents chạy song song cố gắng khóa tệp `.session.json` để cập nhật dữ liệu của mình.

Mặc dù hệ thống đã được cải tiến để lưu trữ phân tách (Hybrid State) vào thư mục `state/` nhưng tệp `.session.json` vẫn được gộp và ghi đè liên tục để phục vụ Visualizer Extension và tương thích ngược. Điều này không giải quyết triệt để hiệu năng I/O và sự cồng kềnh của hệ thống.

## Decision
Quyết định chuyển đổi hoàn toàn sang kiến trúc **Pure Split State** và xóa bỏ vĩnh viễn tệp đĩa `.session.json`. 

Chi tiết thực hiện:
1. Loại bỏ hàm gộp tệp đĩa `aggregate_state` khỏi quy trình lưu trữ trạng thái của Skills.
2. Cập nhật Visualizer Extension để theo dõi (file watcher) sự thay đổi trực tiếp của toàn bộ thư mục `.agents/state/` và thực hiện gộp dữ liệu hiển thị (in-memory aggregation) thay vì đọc tệp `.session.json` tĩnh.
3. Đồng bộ hóa tất cả các CLI commands của Python CLI `workflow_runtime.py` để trực tiếp đọc/ghi các file con trong `state/`.

## Alternatives Considered
1. **Duy trì kiến trúc lai (Hybrid State)**: Vẫn giữ `.session.json` làm bản sao lưu và gộp đĩa. Bị loại bỏ vì không giải quyết được vấn đề overhead đĩa thừa và sự cồng kềnh.
2. **Chỉ sử dụng tệp duy nhất `.session.json`**: Bị loại bỏ vì không khắc phục được lỗi xung đột ghi và tranh chấp khóa của các agent chạy song song.

## Trade-offs
### Pros
- Hiệu năng hệ thống tăng cao nhờ giảm kích thước ghi đĩa trên mỗi lượt chạy của Skill.
- Codebase của phần Skills và CLI sạch sẽ, nhất quán hơn.
- Không còn nguy cơ tranh chấp ghi khóa (file lock conflict) giữa các agents hoạt động song song.

### Cons
- Phải cập nhật đồng loạt cả phía CLI (Python) và Visualizer Extension (TypeScript).
- Các script tiện ích bên ngoài phụ thuộc vào tệp `.session.json` cũ sẽ bị hỏng và cần cập nhật.

## Consequences
- Tệp `.agents/.session.json` không còn được tạo ra.
- Visualizer Extension sẽ theo dõi và xử lý dữ liệu động trực tiếp từ các tệp nhỏ.
- Mã nguồn quản lý trạng thái của AIWF sẽ chỉ thao tác với các tệp JSON nhỏ chuyên biệt (context, workflow, runtime, approvals, usage, agents).

## Risks
- **Risk**: Các script ngoài của người dùng bị lỗi do không tìm thấy `.session.json`.
- **Mitigation**: Cung cấp lệnh CLI `aiwf state status` để xuất dữ liệu gộp định dạng JSON theo yêu cầu (on-demand) cho các công cụ khác sử dụng.

## References
- Brainstorming: [FEAT-028_pure_split_state_management.md](file:///e:/AgentsProject/docs/brainstorming/FEAT-028_pure_split_state_management.md)
- Kế hoạch: [FEAT-028_pure_split_state_management_plan.md](file:///e:/AgentsProject/docs/plans/FEAT-028_pure_split_state_management_plan.md)
