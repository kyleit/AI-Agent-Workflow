<!-- File path: docs/blueprint-governance/BP-QUALITY-GATES.md -->

# BP-QUALITY-GATES: Blueprint Quality Gates & Governance Checklists

Tài liệu này tổng hợp các chốt chặn chất lượng (Quality Gates), ma trận truy vết và các danh sách kiểm tra (Checklists) bắt buộc cho tất cả các thiết kế Blueprint tương lai của AIWF OS.

## 1. Blueprint Quality Gates (Yêu cầu bắt buộc)

Mỗi Blueprint được tạo ra phải chứa đầy đủ các chương mục sau mà không được bỏ sót:
1. **Objective** - Mục tiêu chi tiết.
2. **Scope** - Phạm vi triển khai và ranh giới.
3. **Dependencies** - Danh sách phụ thuộc kỹ thuật.
4. **ADR & FEAT References** - Ánh xạ trực tiếp tới mã số ADR và FEAT.
5. **Runtime Layer** - Xác định rõ lớp nhân, dịch vụ hay daemon.
6. **Public & Internal APIs** - Đặc tả chữ ký hàm và kiểu dữ liệu JSON Schema.
7. **State Model & Machine** - Máy trạng thái và sơ đồ luồng sequence diagrams.
8. **Error Handling & Recovery** - Kịch bản lỗi và cơ chế rollback.
9. **Testing Strategy** - Độ phủ test và kịch bản kiểm thử tự động.

---

## 2. Ma Trận Truy Vết Kiến Trúc (Architectural Traceability Matrix)

### FEAT → ADR → Blueprint Map

| FEAT ID | Dependent ADRs | Target Blueprint Location | Owner |
| :--- | :--- | :--- | :--- |
| **FEAT-086** | ADR-001, ADR-002, ADR-003, ADR-004, ADR-006, ADR-007, ADR-013, ADR-019, ADR-020 | `docs/designs/FEAT-086_blueprint.md` | Architect |
| **FEAT-087** | ADR-005, ADR-014 | `docs/designs/FEAT-087_blueprint.md` | Architect |
| **FEAT-088** | ADR-015, ADR-021, ADR-022, ADR-023, ADR-024, ADR-025, ADR-033 | `docs/designs/FEAT-088_blueprint.md` | Architect |

---

## 3. Blueprint Readiness Checklist (Danh sách kiểm tra sẵn sàng)

- [ ] Toàn bộ các API công khai đều được kiểm tra chữ ký kiểu dữ liệu.
- [ ] Mọi kịch bản lỗi đều có định hướng rollback cụ thể.
- [ ] Không tự ý đưa ra quyết định kiến trúc mới nằm ngoài phạm vi ADR đã duyệt.
- [ ] Tệp JSON Blueprint được tạo đầy đủ và đúng định dạng schema.
