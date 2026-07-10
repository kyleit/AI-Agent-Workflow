<!-- File path: docs/quick/QUICK-001_update_readme_and_default_json.md -->

---
artifact_type: quick-feature
feature_id: QUICK-001
workflow: quick-feature
architecture_impact: low
adr_required: false
status: PASS
---

# Mini Feature Specification – Update README and Default JSON for Three-Scope Metrics

## 1. Feature Goal
Cập nhật tài liệu hướng dẫn `README.md` của Visualizer Extension và logic tạo cấu hình JSON mặc định trong Visualizer Extension để khớp với cấu trúc 3 bảng thống kê sử dụng (Workflow Usage, Project Usage, và Global AI Usage) mới thiết kế.

## 2. Business Value
Giúp các nhà phát triển tích hợp và người dùng hiểu đúng cấu trúc dữ liệu phiên làm việc mới, đồng thời giúp giao diện Visualizer tự động hiển thị đầy đủ cả 3 bảng thống kê với dữ liệu ước tính hợp lý ngay khi khởi tạo phiên mà chưa có dữ liệu đồng bộ từ SQLite.

## 3. Existing Context
- [extension.ts](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/src/extension.ts): Chứa hàm `estimateContextUsage` và logic nạp dữ liệu session ban đầu.
- [README.md](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/README.md): Chứa phần hướng dẫn schema `.session.json` cũ.

## 4. Scope
- **In Scope**:
  - Cập nhật cấu trúc `context_usage` cũ thành 3 nhóm `workflow_usage_summary`, `project_usage_summary`, và `global_usage_summary` trong `extensions/visualizer/README.md`.
  - Nâng cấp hàm `estimateContextUsage` trong `extension.ts` để sinh cấu trúc dữ liệu đầy đủ bao gồm các trường chi tiết.
  - Điền giá trị mặc định cho `project_usage_summary` và `global_usage_summary` trong `extension.ts` nếu chúng chưa có trong session.
- **Out of Scope**: Không thay đổi logic hiển thị giao diện trong `webview.html` hay logic tính toán của bộ đếm phía python.

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [README.md](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/README.md) | Cập nhật tài liệu hướng dẫn JSON Schema mới |
| Modify | [extension.ts](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/src/extension.ts) | Cập nhật ước lượng và cấu hình mặc định ban đầu |

## 6. Proposed Changes

### [README.md](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/README.md)
Thay thế phần `context_usage` và bổ sung các trường còn thiếu (`logs`, `suggested_next_skill`, `suggested_next_command`, `updated_at`, `context_health`) trong schema ví dụ bằng:
```json
  "logs": [
    "> Started blueprint analysis.",
    "> Generated implementation plan docs/plans/FEAT-001_plan.md",
    "> Created visualizer sidebar components."
  ],
  "suggested_next_skill": "implementation-to-debug",
  "suggested_next_command": "debug",
  "updated_at": "2026-07-06T12:41:03Z",
  "context_health": "healthy",
  "workflow_usage_summary": {
    "provider": "antigravity",
    "model": "Gemini 3.5 Flash",
    "input_tokens": 8120400,
    "output_tokens": 68532,
    "cache_tokens": 1218060,
    "thinking_tokens": 4820,
    "active_tokens": 72400,
    "total_tokens": 8188932,
    "limit_tokens": 2000000,
    "percentage": 3.62,
    "estimated_cost_usd": 10.4072,
    "accuracy": "estimated",
    "updated_at": "2026-07-06T12:41:03Z"
  },
  "project_usage_summary": {
    "input_tokens": 8120400,
    "output_tokens": 68532,
    "cache_tokens": 1218060,
    "thinking_tokens": 4820,
    "total_tokens": 8188932,
    "estimated_cost_usd": 10.4072,
    "updated_at": "2026-07-06T12:41:03Z"
  },
  "global_usage_summary": {
    "input_tokens": 12450200,
    "output_tokens": 98532,
    "cache_tokens": 1860240,
    "thinking_tokens": 9480,
    "total_tokens": 12548732,
    "estimated_cost_usd": 15.9872,
    "updated_at": "2026-07-06T12:41:03Z"
  }
```

### [extension.ts](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/src/extension.ts)
1. Cập nhật kiểu trả về và nội dung sinh của `estimateContextUsage`:
```typescript
    private estimateContextUsage(checkpoint: number, conversationId?: string): any {
        const limit_tokens = 2000000;
        let active_tokens = 0;
        let total_tokens = 0;
        try {
            const homeDir = os.homedir();
            const brainPath = path.join(homeDir, '.gemini', 'antigravity-ide', 'brain');
            if (fs.existsSync(brainPath)) {
                let latestFile = '';

                if (conversationId) {
                    const exactLogFile = path.join(brainPath, conversationId, '.system_generated', 'logs', 'transcript.jsonl');
                    if (fs.existsSync(exactLogFile)) {
                        latestFile = exactLogFile;
                    }
                }

                if (!latestFile) {
                    const subfolders = fs.readdirSync(brainPath);
                    let latestMtime = 0;

                    subfolders.forEach(folder => {
                        const logFile = path.join(brainPath, folder, '.system_generated', 'logs', 'transcript.jsonl');
                        if (fs.existsSync(logFile)) {
                            const stat = fs.statSync(logFile);
                            if (stat.mtimeMs > latestMtime) {
                                latestMtime = stat.mtimeMs;
                                latestFile = logFile;
                            }
                        }
                    });
                }

                if (latestFile) {
                    const fileSize = fs.statSync(latestFile).size;
                    active_tokens = Math.min(Math.round(fileSize / 3), limit_tokens);
                    total_tokens = Math.min(active_tokens + 20000, limit_tokens);
                }
            }
        } catch (e) {
            console.error('Failed to estimate dynamically from log:', e);
        }

        if (total_tokens === 0) {
            const percentage = Math.min(checkpoint * 8.5, 95);
            active_tokens = Math.round((percentage / 100) * limit_tokens);
            total_tokens = active_tokens;
        }

        const percentage = Math.min((active_tokens / limit_tokens) * 100, 100);

        return {
            provider: "antigravity",
            model: "auto",
            input_tokens: Math.round(total_tokens * 0.98),
            output_tokens: Math.round(total_tokens * 0.02),
            cache_tokens: Math.round(total_tokens * 0.15),
            thinking_tokens: Math.round(total_tokens * 0.005),
            active_tokens: active_tokens,
            total_tokens: total_tokens,
            limit_tokens: limit_tokens,
            percentage: parseFloat(percentage.toFixed(2)),
            estimated_cost_usd: parseFloat((total_tokens * 1.5 / 1000000).toFixed(4)),
            accuracy: "estimated",
            updated_at: new Date().toISOString()
        };
    }
```
2. Cập nhật phần nạp session data:
```typescript
                const checkpointNum = typeof session.checkpoint === 'number' ? session.checkpoint : 1;
                if (!session.workflow_usage_summary || Object.keys(session.workflow_usage_summary).length === 0 || !session.workflow_usage_summary.total_tokens) {
                    session.workflow_usage_summary = this.estimateContextUsage(checkpointNum, session.conversation_id);
                }
                if (!session.context_usage) {
                    session.context_usage = session.workflow_usage_summary;
                }
                if (!session.project_usage_summary) {
                    session.project_usage_summary = {
                        input_tokens: session.workflow_usage_summary.input_tokens || 0,
                        output_tokens: session.workflow_usage_summary.output_tokens || 0,
                        cache_tokens: session.workflow_usage_summary.cache_tokens || 0,
                        thinking_tokens: session.workflow_usage_summary.thinking_tokens || 0,
                        total_tokens: session.workflow_usage_summary.total_tokens || 0,
                        estimated_cost_usd: session.workflow_usage_summary.estimated_cost_usd || 0.0,
                        updated_at: session.workflow_usage_summary.updated_at || new Date().toISOString()
                    };
                }
                if (!session.global_usage_summary) {
                    session.global_usage_summary = {
                        input_tokens: session.project_usage_summary.input_tokens || 0,
                        output_tokens: session.project_usage_summary.output_tokens || 0,
                        cache_tokens: session.project_usage_summary.cache_tokens || 0,
                        thinking_tokens: session.project_usage_summary.thinking_tokens || 0,
                        total_tokens: session.project_usage_summary.total_tokens || 0,
                        estimated_cost_usd: session.project_usage_summary.estimated_cost_usd || 0.0,
                        updated_at: session.project_usage_summary.updated_at || new Date().toISOString()
                    };
                }
```

## 7. Risks
- **Risk**: Định dạng thời gian `ISO8601` dạng chuỗi trong Javascript khác múi giờ Python. → **Mitigation**: Cả webview và extension đều xử lý tốt các định dạng thời gian chuẩn ISO.

## 8. Acceptance Criteria
- [ ] Tệp `README.md` hiển thị đúng cấu trúc JSON mới cho cả 3 bảng thống kê.
- [ ] Khi khởi chạy Extension với file session thiếu trường `workflow_usage_summary`, các trường mặc định được khởi tạo chính xác.
- [ ] Cả 3 bảng thống kê đều hiển thị các thông số ước tính mặc định trên giao diện Visualizer khi chưa đồng bộ.

## 9. Test Plan
- **Verification**: Chạy `npm run compile` trong thư mục `extensions/visualizer/`.
- **Manual Check**: Mở Visualizer Extension và kiểm tra xem cả 3 bảng thống kê có được hiển thị đầy đủ thông số ước tính ban đầu hay không.
