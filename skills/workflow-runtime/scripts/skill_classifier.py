# skill_classifier.py
import re

def classify_intent(request: str) -> dict:
    req_lower = request.lower()
    
    # 1. Check for release commands (must be explicit)
    release_keywords = ["release", "bump version", "changelog", "git tag", "git push tag", "đẩy release", "cập nhật changelog", "version bump"]
    is_release_explicit = any(kw in req_lower for kw in release_keywords)
    if is_release_explicit:
        return {
            "status": "success",
            "recommended_skill": "implementation-to-release",
            "recommended_command": "release",
            "options": [],
            "reason": "Yêu cầu thực hiện quy trình phát hành hoặc đóng gói phiên bản (Release)."
        }
        
    # 2. Memory bootstrap vs update
    if any(kw in req_lower for kw in ["initialize memory", "bootstrap memory", "khởi tạo memory", "khởi tạo bộ nhớ"]):
        return {
            "status": "success",
            "recommended_skill": "project-memory-bootstrap",
            "recommended_command": "bootstrap",
            "options": [],
            "reason": "Yêu cầu khởi tạo bộ nhớ dự án từ đầu."
        }
    if any(kw in req_lower for kw in ["refresh memory", "sync memory", "update memory", "cập nhật bộ nhớ", "đồng bộ bộ nhớ"]):
        return {
            "status": "success",
            "recommended_skill": "project-memory-update",
            "recommended_command": "update",
            "options": [],
            "reason": "Yêu cầu cập nhật/đồng bộ bộ nhớ dự án dựa trên thay đổi."
        }
        
    # 3. RAG Search
    if any(kw in req_lower for kw in ["how does this project", "where is", "tìm file", "tìm hàm", "hỏi về kiến trúc", "cấu trúc dự án thế nào"]):
        return {
            "status": "success",
            "recommended_skill": "project-rag-search",
            "recommended_command": "search",
            "options": [],
            "reason": "Yêu cầu tìm kiếm tri thức hoặc kiến trúc dự án."
        }
        
    # 4. Implement from blueprint
    if any(kw in req_lower for kw in ["implement from blueprint", "thực hiện từ blueprint", "code theo thiết kế", "code blueprint"]):
        return {
            "status": "success",
            "recommended_skill": "blueprint-to-implementation",
            "recommended_command": "implement",
            "options": [],
            "reason": "Yêu cầu hiện thực hóa mã nguồn từ Blueprint thiết kế đã duyệt."
        }
        
    # 5. Debug compilation/test failures
    if any(kw in req_lower for kw in ["debug build", "debug test", "sửa lỗi biên dịch", "sửa lỗi test"]):
        return {
            "status": "success",
            "recommended_skill": "implementation-to-debug",
            "recommended_command": "debug",
            "options": [],
            "reason": "Yêu cầu debug các lỗi phát sinh khi chạy build/test."
        }
        
    # 6. Verify implementation
    if any(kw in req_lower for kw in ["verify implementation", "kiểm thử tính năng", "xác minh code"]):
        return {
            "status": "success",
            "recommended_skill": "debug-to-verify",
            "recommended_command": "verify",
            "options": [],
            "reason": "Yêu cầu kiểm thử và xác minh tính năng sau khi hoàn thành."
        }
        
    # 7. Bug / Error / Exception
    bug_keywords = ["bug", "error", "exception", "failed", "broken", "lỗi", "crash", "hỏng"]
    is_bug = any(kw in req_lower for kw in bug_keywords)
    
    # 8. Feature / UI improvements
    small_feat_keywords = ["button", "endpoint", "filter", "search", "export", "ui block", "config option", "thêm nút", "thêm api", "thêm trường"]
    is_small_feat = any(kw in req_lower for kw in small_feat_keywords)
    
    large_feat_keywords = ["new system", "new module", "new workflow", "architecture change", "database design", "tái cấu trúc", "hệ thống mới", "thiết kế database", "cơ sở dữ liệu", "thiết kế cơ sở dữ liệu", "tái thiết kế"]
    is_large_feat = any(kw in req_lower for kw in large_feat_keywords)
    
    # 9. Scenarios mapping
    if is_bug:
        if is_large_feat or any(kw in req_lower for kw in ["broad", "unclear", "architectural"]):
            return {
                "status": "success",
                "recommended_skill": "brainstorming",
                "recommended_command": "brainstorm",
                "options": [],
                "reason": "Lỗi phức tạp liên quan đến cấu trúc hệ thống hoặc yêu cầu rộng, cần brainstorming thiết kế."
            }
        return {
            "status": "success",
            "recommended_skill": "quick-fix",
            "recommended_command": "fix",
            "options": [],
            "reason": "Lỗi cục bộ, rủi ro thấp, thích hợp với quy trình sửa lỗi nhanh (quick-fix)."
        }
        
    if is_large_feat:
        return {
            "status": "success",
            "recommended_skill": "brainstorming",
            "recommended_command": "brainstorm",
            "options": [],
            "reason": "Tính năng lớn, thay đổi kiến trúc hoặc cơ sở dữ liệu, cần thảo luận yêu cầu trước (brainstorming)."
        }
        
    if is_small_feat:
        return {
            "status": "success",
            "recommended_skill": "quick-feature",
            "recommended_command": "feature",
            "options": [],
            "reason": "Yêu cầu thêm tính năng nhỏ hoặc cải tiến giao diện cục bộ (quick-feature)."
        }
        
    # 10. Ambiguous fallback
    return {
        "status": "success",
        "recommended_skill": "ambiguous",
        "recommended_command": "",
        "options": ["quick-fix", "quick-feature", "brainstorming"],
        "reason": "Yêu cầu chưa rõ ràng hoặc chứa từ khóa chung chung, cần người dùng lựa chọn quy trình."
    }
