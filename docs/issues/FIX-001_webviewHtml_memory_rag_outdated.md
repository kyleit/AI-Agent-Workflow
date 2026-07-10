<!-- File path: docs/issues/FIX-001_webviewHtml_memory_rag_outdated.md -->

---
artifact_type: fix
issue_id: FIX-001
workflow: quick-fix
architecture_impact: low
adr_required: false
status: draft
---

# Fix Document - webviewHtml.ts Outdated: Memory Status & RAG hien thi sai

## 1. Issue
Trong giao dien Visualizer extension, phan Memory Status card luon hien thi:
- Status: UNKNOWN
- Last Sync: N/A
- RAG: none

Du `.agents/.session.json` thuc te chua day du du lieu `memory.status = "HEALTHY"`, `memory.last_updated`, `rag.connected = true`, `rag.provider = "qdrant"`.

## 2. Symptoms
- Memory Status card khong bao gio cap nhat, luon hien thi gia tri fallback
- RAG field hien thi `none` thay vi `qdrant`
- Cac truong khac nhu item-id, item-desc, stepper hoat dong binh thuong

## 3. Root Cause
Extension TypeScript (`extension.ts`) serve HTML tu `webviewHtml.ts` (import `webviewHtml`), khong phai tu file `resources/webview.html`.

File `webviewHtml.ts` la ban **snapshot cu** cua HTML - no **thieu** cac DOM element va render logic cho Memory Status:
- Khong co `<li>Status: <strong id="memory-status">...`
- Khong co `<li>Last Sync: <strong id="memory-sync">...`
- Khong co `<li>RAG: <strong id="rag-status">...`
- Khong co JS: `document.getElementById("memory-status").innerText = ...`

Khi extension gui UPDATE_SESSION message voi day du data, webview JS co getElementById("memory-status") nhung tra ve null vi DOM element khong ton tai trong HTML cu -> silent error.

## 4. Scope
- **In Scope**: Sync lai noi dung `webviewHtml.ts` tu `resources/webview.html` hien tai
- **Out of Scope**: Khong refactor cach extension load HTML, khong thay doi extension.ts, khong thay doi session schema

## 5. Expected Files

| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | `extensions/visualizer/src/webviewHtml.ts` | Sync toan bo HTML content tu `resources/webview.html` |

## 6. Proposed Fix

Thay the toan bo noi dung string trong `webviewHtml.ts` bang noi dung hien tai cua `resources/webview.html`.

Cu the:
1. Doc toan bo noi dung `resources/webview.html`
2. Escape cac backtick va ${ trong HTML content
3. Boc trong `export const webviewHtml = \`...\`;`
4. Ghi lai `src/webviewHtml.ts`

## 7. Risks
- **Risk**: webviewHtml.ts co the lai bi out-of-sync trong tuong lai
- **Mitigation**: Sau fix, xem xet them build script tu dong sync tu webview.html vao webviewHtml.ts

## 8. Acceptance Criteria
- [ ] Memory Status card hien thi Status: HEALTHY (doc tu session)
- [ ] Last Sync hien thi thoi gian cu the tu memory.last_updated
- [ ] RAG hien thi qdrant (hoac provider thuc te)
- [ ] Rebuild extension khong bi loi compile

## 9. Test Plan
- **Verification**: `cd extensions/visualizer && npm run compile` - khong loi
- **Manual Check**: Reload extension trong VS Code -> kiem tra Memory Status card
- **Unit Tests**: Khong co unit test rieng cho webview HTML
