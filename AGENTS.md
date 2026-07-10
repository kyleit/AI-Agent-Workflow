<!-- AIWF:RULES:BEGIN -->
# AI Engineering Workflow Agents

Every AI agent working inside this project **MUST** follow the AI Workflow Framework.

## Primary Workflow

Before executing any task:

1. Load and follow all policies defined in AI_RULES.md (the single source of truth).
2. Load the workflow resources from:

   * .agents/skills/
   * .agents/runtime/
   * .agents/templates/
3. Use the matching workflow Skill whenever one exists.
4. Respect runtime checkpoints and resume rules.
5. Never bypass approval gates or other framework policies.
6. Use `.agents/state/` sub-states and CLI `state` commands to inspect or restore system status.

## Global Policies

The following policies are defined in AI_RULES.md and apply to every task:

1. Approval Gate Policy
2. Git Workflow Policy
3. Memory First Policy
4. RAG Policy
5. Artifact Policy
6. Versioning Policy
7. Documentation Policy
8. Testing Policy
9. Release Policy
10. Workflow Phase Separation Policy
11. Absolute Path Prohibition Policy

AI_RULES.md is the **single source of truth** for all shared framework behavior. If any instruction conflicts with another document, follow AI_RULES.md.

---

## Agent Catalog

The framework divides agents into **Core Phase Owners** and **Specialist Assistants**:

### 1. Core Phase Owners
- **Planner**: converts brainstorming to plans.
- **Architect**: converts plans to design blueprints.
- **Coder**: modifies codebase.
- **Reviewer**: audits code and test output.
- **Release Manager**: handles versioning and publish tasks.

### 2. Specialist Groups
- **Discovery**: Product Analyst, Business Analyst, Requirement Analyst, Research Agent, Memory Analyst, RAG Analyst.
- **Planning**: Dependency Analyst, Risk Analyst, Security Planner, Performance Planner, Test Planner.
- **Architecture**: Backend Architect, Frontend Architect, Database Architect, API Architect, Infrastructure Architect, Security Architect.
- **Implementation**: Backend Developer, Frontend Developer, Database Developer, Infrastructure Developer, DevOps Developer, Migration Developer, Documentation Writer, Test Developer.
- **Review**: Code Reviewer, QA Reviewer, Security Reviewer, Performance Reviewer, Accessibility Reviewer, Architecture Reviewer.
- **Release**: Version Manager, Release Validator, Package Builder, ChangeLog Manager, Publisher.

## Product-Oriented Public Export Changelog Rule
- **Quy tắc viết Changelog cho Public Export**: Sau khi hoàn thành xuất bản mã nguồn bằng lệnh `make export` (hoặc các lệnh tương tự sang thư mục `public_export`), Agent **BẮT BUỘC** phải tạo/cập nhật tệp `CHANGELOG.md` riêng cho kho xuất bản công khai nằm trong thư mục `public_export/CHANGELOG.md`. Nội dung của tệp Changelog này phải được viết lại hoàn toàn dựa trên Changelog của dự án chính, định hướng theo góc nhìn sản phẩm (Product-oriented) thay vì góc nhìn kỹ thuật chi tiết, dễ hiểu đối với người dùng cuối, và **chỉ** ghi nhận các thay đổi thực sự có mặt trong mã nguồn xuất bản công khai.

GitHub Repository: https://github.com/kyleit/AI-Agent-Workflow
<!-- AIWF:RULES:END -->
