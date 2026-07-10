---
feature_id: FEAT-046
feature_name: Upgrade Brainstorming Skill to v3
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-046_upgrade_brainstorming_skill_to_v3_plan.md
---

# Master Requirement Document – Upgrade Brainstorming Skill to v3

## 1. Feature ID & Name
- **Feature ID**: FEAT-046
- **Feature Name**: Upgrade Brainstorming Skill to v3 (Master Requirement Discovery)

## 2. Original Idea
Nâng cấp kỹ năng `brainstorming` từ một công cụ phát hiện yêu cầu đơn giản thành một bộ máy Động não Tri thức Chủ chốt (Master Requirement Discovery) giàu thông tin hơn để loại bỏ sự lặp lại phân tích trong các pha Lập kế hoạch (Planning) và Bản thiết kế kỹ thuật (Blueprint).

## 3. Business Problem
- **Problem**: Các pha lập kế hoạch (Plan) và thiết kế kỹ thuật (Blueprint) ở hạ nguồn hiện đang lặp lại các hoạt động phân tích kiến trúc, rủi ro và phạm vi. Sự trùng lặp suy luận này gây lãng phí mã thông báo (tokens), tăng chi phí và dễ gây mất nhất quán thông tin trong quy trình SDLC.
- **Why it matters**: Làm chậm tiến trình thực thi của các subagent, tăng chi phí vận hành mô hình và giảm độ tin cậy của các artifact được tạo ra.
- **Who is affected**: Tất cả các AI Agent tham gia vào chuỗi SDLC (Planner, Architect, Coder) và người dùng giám sát quy trình.
- **Expected outcome**: Pha brainstorming v3 cung cấp đầy đủ thông tin về rủi ro, phân tích tài sản sẵn có, vùng ảnh hưởng, nguyên tắc thiết kế, giúp các pha sau thừa hưởng trực tiếp mà không cần phân tích lại.

## 4. Requirement Discovery
- **Functional Requirements**:
  - **FR-01**: Bảo toàn mọi tính năng cũ (làm rõ yêu cầu, tính Readiness Score, so sánh giải pháp).
  - **FR-02**: Bổ sung các phần phân tích tri thức mới: Scope Boundary, Existing Asset Analysis, Dependency & Blast Radius, Migration Strategy, Architecture Principles, Non Goals, Success Metrics, Risk Matrix, Technical Questions, ADR Detection, Test Strategy Preview, Extension Impact, Complexity Estimation, Roadmap Alignment.
  - **FR-03**: Điều chỉnh tệp hướng dẫn Planning (`brainstorming-to-plan`) chỉ tập trung vào phân chia giai đoạn công việc, ước lượng thời gian, lập lịch trình và phụ thuộc.
  - **FR-04**: Điều chỉnh tệp hướng dẫn Blueprint (`plan-to-blueprint`) kế thừa trực tiếp các nguyên tắc thiết kế và khuyến nghị ADR từ tài liệu Brainstorming v3.
- **Non-functional Requirements**:
  - **NFR-01**: Tối ưu hóa token bằng cách loại bỏ trùng lặp phân tích.
  - **NFR-02**: Đảm bảo khả năng tương thích ngược cho các tài liệu brainstorming v2.
- **Technical Constraints**:
  - **TC-01**: Cập nhật trực tiếp tệp hướng dẫn kỹ năng `SKILL.md` và templates của hệ thống.

## 5. Scope Boundary
- **In Scope**:
  - Thiết kế lại cấu trúc khuôn mẫu (Template) trong [skills/brainstorming/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming/SKILL.md) để hỗ trợ sinh 14 mục phân tích tri thức mới.
  - Tối ưu hóa [skills/brainstorming-to-plan/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming-to-plan/SKILL.md) và [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md).
- **Out of Scope**: Thay đổi cách CLI Python của `workflow-runtime` xác thực checkpoint cơ bản hoặc thay đổi giao diện webview của extension.
- **Deferred Scope**: Tự động sinh biểu đồ đồ thị liên kết tri thức sang Obsidian dạng ảnh trực tiếp.
- **Future Scope**: Tích hợp phân tích chất lượng tri thức bằng agent chuyên biệt (Quality Agent).

## 6. Existing Asset Analysis
- [skills/brainstorming/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming/SKILL.md): **Extend** - Bổ sung các chỉ dẫn tạo các phần phân tích mới vào quy trình làm việc và mẫu Markdown.
- [skills/brainstorming-to-plan/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming-to-plan/SKILL.md): **Refactor** - Loại bỏ các hướng dẫn yêu cầu Planner phân tích lại kiến trúc hoặc phân tích rủi ro hệ thống; hướng dẫn Planner chỉ tập trung lập lịch, chia phase, và ước lượng nguồn lực.
- [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md): **Refactor** - Thay đổi chỉ dẫn để thiết kế kỹ thuật kế thừa trực tiếp Blast Radius, ADR recommendations và các câu hỏi kỹ thuật từ tài liệu brainstorm v3.

## 7. Dependency & Blast Radius Analysis
- **Affected skills**: `brainstorming` (Cao), `brainstorming-to-plan` (Trung bình), `plan-to-blueprint` (Trung bình).
- **Affected documentation**: Tệp hướng dẫn sử dụng và tài liệu giới thiệu hệ thống kỹ năng.
- **Impact Level**: Trung bình (Medium) - Chỉ thay đổi các tệp cấu hình hướng dẫn kỹ năng (SKILL.md) ở các pha đầu, không ảnh hưởng đến mã nguồn thực thi chính hoặc cơ sở dữ liệu của dự án.

## 8. Migration Strategy
- **Backward compatibility**: Các tài liệu brainstorming phiên bản cũ (v2) thiếu các phần phân tích mới vẫn được xử lý bình thường bởi Planner và Architect; các mô hình sẽ tự động bỏ qua các trường bị thiếu và áp dụng giá trị mặc định (N/A hoặc None).
- **Coexistence period**: Cả tài liệu dạng v2 và v3 đều tồn tại song song được trong thư mục `docs/brainstorming/`.

## 9. Architecture Principles
- **API First**: Các giao diện đầu ra của tài liệu được định nghĩa rõ ràng.
- **Memory First**: Trước khi lập brainstorm, AI Agent phải kiểm tra Project Memory và RAG để kế thừa bối cảnh thiết kế hiện tại.
- **Backward Compatibility**: Nâng cấp không phá vỡ khả năng đọc hiểu của các Skill hạ nguồn.

## 10. Non Goals
- Kế hoạch này sẽ **KHÔNG** làm thay đổi cơ chế kiểm tra checkpoint hoạt động của CLI `workflow_runtime.py`.
- Sẽ **KHÔNG** viết lại mã nguồn cốt lõi của extension trong đợt cập nhật này.

## 11. Success Metrics
- **Token reduction**: Giảm từ 15-25% số lượng tokens sử dụng trong pha lập kế hoạch (Plan) và bản thiết kế (Blueprint) do không cần yêu cầu mô hình phân tích lại các rủi ro, cấu trúc hệ thống.
- **Expected ROI**: Tiết kiệm chi phí vận hành API và tăng tốc độ xử lý của agent lên 20%.

## 12. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
|---|---|---|---|---|
| Mô hình AI đời cũ không tuân thủ được hết 14 phần phân tích mới | Low | Medium | Thêm ví dụ đầu ra (Few-shot examples) chi tiết trong SKILL.md | Architect |
| Phá vỡ định dạng phân tích của Planner | Low | Low | Chạy thử nghiệm tự động trên nhiều loại yêu cầu khác nhau trước khi release | Reviewer |

## 13. Technical Questions
- Làm thế nào để tự động điền phần ADR Detection chính xác mà không gây nhầm lẫn cho Architect?
- Làm thế nào để thiết lập kiểm thử tự động (Unit test) trực tiếp cho cấu trúc dữ liệu của tệp Markdown mới?

## 14. ADR Detection
- **ADR Required**: Yes.
- **Rationale**: Cần ghi nhận tài liệu ADR-011 để lưu lại quyết định thay đổi cấu trúc tài liệu Master Requirement Document v3 trên toàn bộ hệ thống kỹ năng của AIWF.

## 15. Test Strategy Preview
- **Regression Tests**: Kiểm thử chạy lại các dự án cũ có tài liệu brainstorm v2 để xác nhận Planner vẫn biên dịch ra Plan bình thường.
- **Compatibility Tests**: Xác nhận tài liệu brainstorm v3 được đọc hiểu chính xác bởi Planner v3 và Architect v3.

## 16. Extension Impact
- **Visualizer Extension**: Không ảnh hưởng trực tiếp đến UI sidebar vì extension chỉ watch tệp tin trạng thái `.agents/state/` chứ không trực tiếp đọc nội dung tệp Markdown brainstorming.

## 17. Complexity Estimation
- **Implementation Complexity**: Thấp-Trung bình (Low-Medium).
- **Files affected**: 3 tệp (`skills/brainstorming/SKILL.md`, `skills/brainstorming-to-plan/SKILL.md`, `skills/plan-to-blueprint/SKILL.md`).
- **Refactoring percentage**: ~10% mã nguồn hướng dẫn kỹ năng.

## 18. Roadmap Alignment
- Nằm trong giai đoạn nâng cấp tối ưu hóa hiệu năng và chất lượng tri thức của AIWF framework.

## 19. Solution Options Evaluated
*(Đã được phân tích chi tiết trong hội thoại, thống nhất chọn Phương án A - Cập nhật trực tiếp và tích hợp phiên bản)*

## 20. Selected Solution
- **Choice**: Option A — Update SKILL.md directly and integrate with versioning
- **Why Selected**: Giản tiện cấu trúc thư mục dự án, không gây phân mảnh hệ thống kỹ năng, tối ưu chi phí bảo trì lâu dài.

## 21. Acceptance Criteria
- [ ] Tệp [skills/brainstorming/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming/SKILL.md) được cập nhật chứa đầy đủ hướng dẫn sinh 14 mục phân tích mới.
- [ ] Tệp [skills/brainstorming-to-plan/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/brainstorming-to-plan/SKILL.md) và [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md) được cập nhật tinh giản, loại bỏ hoàn toàn các phân tích lặp lại.
- [ ] Kiểm thử tự động trên tài liệu brainstorming v2 và v3 đều vượt qua (Pass).

## 22. Final Planning Prompt
*(Chi tiết thông tin đầu vào phục vụ cho kỹ năng `brainstorming-to-plan` để tiến hành lập kế hoạch di chuyển và nâng cấp hệ thống kỹ năng sang v3).*
