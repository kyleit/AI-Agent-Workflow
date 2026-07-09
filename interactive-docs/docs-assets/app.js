// File path: docs/docs-assets/app.js

document.addEventListener("DOMContentLoaded", () => {
  initRouter();
  initSkillsCatalog();
  initSimulator();
});

// ==========================================
// 1. ROUTER SYSTEM (TAB SWITCHING)
// ==========================================
function initRouter() {
  const menuButtons = document.querySelectorAll(".menu-item button");
  const tabContents = document.querySelectorAll(".tab-content");
  const headerTitle = document.querySelector(".header-title h1");

  menuButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      
      // Update sidebar menu active state
      document.querySelectorAll(".menu-item").forEach(item => item.classList.remove("active"));
      btn.parentElement.classList.add("active");

      // Update active content tab
      tabContents.forEach(tab => {
        tab.classList.remove("active");
        if (tab.id === targetTab) {
          tab.classList.add("active");
        }
      });

      // Update Header Title
      const tabTitleMap = {
        "overview": "Tổng quan AI Workflow",
        "workflows": "Hướng dẫn Quy trình phát triển (SDLC Flows)",
        "skills": "Thư mục Skills chi tiết (Skills Directory)",
        "runtime": "Hướng dẫn vận hành CLI Runtime",
        "simulator": "Trình giả lập SDLC tương tác (SDLC Simulator)",
        "obsidian": "Hướng dẫn tích hợp Obsidian (Obsidian Vault Setup)"
      };
      headerTitle.textContent = tabTitleMap[targetTab] || "Tài liệu AI Skill Framework";
      
      // Tự động đóng menu trên mobile khi click chọn mục
      const menuList = document.querySelector(".menu-list");
      if (menuList) {
        menuList.classList.remove("show");
      }
    });
  });

  // Xử lý sự kiện click nút hamburger toggle trên mobile
  const menuToggle = document.getElementById("menuToggle");
  const menuList = document.querySelector(".menu-list");
  if (menuToggle && menuList) {
    menuToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      menuList.classList.toggle("show");
    });
    
    // Đóng menu khi nhấp ra ngoài vùng hoạt động
    document.addEventListener("click", (e) => {
      if (!menuToggle.contains(e.target) && !menuList.contains(e.target)) {
        menuList.classList.remove("show");
      }
    });
  }

  // Inner tabs for Workflows Guide page
  const flowTabBtns = document.querySelectorAll(".flow-tab-btn");
  const flowPanels = document.querySelectorAll(".flow-panel");

  flowTabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetFlow = btn.getAttribute("data-flow");

      flowTabBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      flowPanels.forEach(panel => {
        panel.style.display = "none";
        if (panel.id === targetFlow) {
          panel.style.display = "block";
        }
      });
    });
  });
}

// ==========================================
// 2. SKILLS CATALOG (RENDER, SEARCH, FILTER)
// ==========================================
let currentFilterCategory = "all";
let currentSearchQuery = "";

function initSkillsCatalog() {
  const grid = document.querySelector(".skills-grid");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const searchInput = document.querySelector("#skillSearch");

  function renderSkills() {
    grid.innerHTML = "";
    
    const filtered = skillsData.filter(skill => {
      const matchesCategory = currentFilterCategory === "all" || skill.category === currentFilterCategory;
      const matchesSearch = skill.name.toLowerCase().includes(currentSearchQuery) || 
                            skill.command.toLowerCase().includes(currentSearchQuery) ||
                            skill.purpose.toLowerCase().includes(currentSearchQuery);
      return matchesCategory && matchesSearch;
    });

    if (filtered.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 48px; color: var(--muted);">Không tìm thấy skill nào khớp với điều kiện tìm kiếm.</div>`;
      return;
    }

    filtered.forEach(skill => {
      const card = document.createElement("div");
      card.className = "skill-card";
      card.innerHTML = `
        <div class="skill-card-header">
          <span class="skill-badge">${skill.category.toUpperCase()}</span>
          <span style="color: var(--cyan); font-weight: 700; font-family: monospace;">${skill.command}</span>
        </div>
        <h3>${skill.name}</h3>
        <p class="skill-desc">${skill.purpose}</p>
        <div class="skill-metadata">
          <div class="meta-row">
            <span class="meta-label">Checkpoint SDLC:</span>
            <span class="meta-value">${skill.checkpoint}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Tham số đầu vào:</span>
            <span class="meta-value" style="font-family: monospace; font-size: 10px;">${skill.input}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Sản phẩm đầu ra:</span>
            <span class="meta-value" style="font-size: 11px;">${skill.output}</span>
          </div>
          <div class="meta-row" style="margin-top: 6px; border-top: 1px dashed rgba(255,255,255,0.05); padding-top: 6px; flex-direction: column;">
            <span class="meta-label" style="color: var(--orange); margin-bottom: 2px;">⚠️ Lưu ý (Pitfall):</span>
            <span class="meta-value" style="color: var(--muted); font-size: 11px; font-weight: normal; line-height: 1.4;">${skill.pitfall}</span>
          </div>
        </div>
      `;
      grid.appendChild(card);
    });
  }

  // Handle Search Input
  searchInput.addEventListener("input", (e) => {
    currentSearchQuery = e.target.value.toLowerCase();
    renderSkills();
  });

  // Handle Category Filter Buttons
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilterCategory = btn.getAttribute("data-category");
      renderSkills();
    });
  });

  // Initial Render
  renderSkills();
}

// ==========================================
// 3. COPY TO CLIPBOARD HELPER
// ==========================================
window.copyToClipboard = function(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    const originalText = btnElement.textContent;
    btnElement.textContent = "Đã copy!";
    btnElement.style.color = "var(--green)";
    btnElement.style.borderColor = "var(--green)";
    setTimeout(() => {
      btnElement.textContent = originalText;
      btnElement.style.color = "";
      btnElement.style.borderColor = "";
    }, 1500);
  });
};

// ==========================================
// 4. INTERACTIVE WORKFLOW SIMULATOR
// ==========================================
let simCurrentWorkflow = "standard";
let simCurrentStepIndex = 0;

const simStepsData = {
  standard: [
    {
      title: "Khởi tạo (Initialize)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 1",
      agentAction: "Phân tích cấu trúc thư mục, phát hiện Git repository và khởi tạo tệp phiên làm việc `.agents/.session.json` ở chế độ Sandbox.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 1" },
        { type: "success", text: "Session initialized with permission_mode=sandbox." },
        { type: "output", text: "Created session database entry. Status: active. Checkpoint: 1." }
      ]
    },
    {
      title: "Đồng bộ bộ nhớ (Memory Sync)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Syncing project memory\" && python skills/workflow-runtime/scripts/workflow_runtime.py usage sync",
      agentAction: "Quét git diff, lập danh sách thay đổi và đồng bộ vào cơ sở dữ liệu vector RAG.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Syncing project memory\"" },
        { type: "output", text: "Step updated: Syncing project memory." },
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py usage sync" },
        { type: "success", text: "Usage database synchronized successfully. Context Usage: 2.06%." }
      ]
    },
    {
      title: "Khảo sát ý tưởng (Brainstorm)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming\" --command \"brainstorm\" --checkpoint 3 --step \"Brainstorming feature solution\"",
      agentAction: "Khảo sát cấu trúc mã nguồn, thiết kế giải pháp sơ bộ và tạo tệp đặc tả ý tưởng `docs/brainstorming/FEAT-015_interactive_docs.md`.",
      gate: "approval",
      gateText: "Approve brainstorming specification for FEAT-015? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming\" --command \"brainstorm\" --checkpoint 3 --step \"Brainstorming feature solution\"" },
        { type: "output", text: "Skill brainstorming started. Active Feature: FEAT-015." },
        { type: "output", text: "Writing brainstorming file: docs/brainstorming/FEAT-015_interactive_docs.md..." },
        { type: "warn", text: "Approve brainstorming specification for FEAT-015? [Y/N]" }
      ]
    },
    {
      title: "Lập kế hoạch (Planning)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming-to-plan\" --command \"plan\" --checkpoint 4 --step \"Creating implementation plan\"",
      agentAction: "Xây dựng kế hoạch thực thi, lập file `implementation_plan.md` ở tầng IDE và đồng bộ vào dự án tại `docs/plans/FEAT-015_interactive_docs_plan.md` cùng file danh sách công việc `task.md`.",
      gate: "approval",
      gateText: "Approve Implementation Plan for FEAT-015? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming-to-plan\" --command \"plan\" --checkpoint 4 --step \"Creating implementation plan\"" },
        { type: "output", text: "Creating implementation plan..." },
        { type: "success", text: "Plan synchronized: docs/plans/FEAT-015_interactive_docs_plan.md created." },
        { type: "warn", text: "Approve Implementation Plan for FEAT-015? [Y/N]" }
      ]
    },
    {
      title: "Thiết kế kỹ thuật (Blueprint)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"plan-to-blueprint\" --command \"blueprint\" --checkpoint 5 --step \"Drafting blueprint\" && python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-015_interactive_docs_blueprint.md",
      agentAction: "Thiết kế chi tiết cấu trúc các tệp tin mới, chữ ký hàm, phông nền CSS và định nghĩa Javascript trước khi lập trình. Đăng ký blueprint lên CLI.",
      gate: "approval",
      gateText: "Approve Blueprint docs/designs/FEAT-015_interactive_docs_blueprint.md? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"plan-to-blueprint\" --command \"blueprint\" --checkpoint 5 --step \"Drafting blueprint\"" },
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-015_interactive_docs_blueprint.md" },
        { type: "success", text: "Blueprint docs/designs/FEAT-015_interactive_docs_blueprint.md registered." },
        { type: "warn", text: "Approve Blueprint docs/designs/FEAT-015_interactive_docs_blueprint.md? [Y/N]" }
      ]
    },
    {
      title: "Viết code (Implementation)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"blueprint-to-implementation\" --command \"implement\" --checkpoint 6 --step \"Writing code files\"",
      agentAction: "Thực thi viết mã nguồn, tạo mới các tệp `index.html`, `style.css`, `app.js` và `skills-data.js` dựa theo đúng thiết kế của Blueprint đã phê duyệt.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"blueprint-to-implementation\" --command \"implement\" --checkpoint 6 --step \"Writing code files\"" },
        { type: "output", text: "Writing /Volumes/Kyle/AgentsProject/docs/index.html..." },
        { type: "output", text: "Writing /Volumes/Kyle/AgentsProject/docs/docs-assets/style.css..." },
        { type: "output", text: "Writing /Volumes/Kyle/AgentsProject/docs/docs-assets/app.js..." },
        { type: "success", text: "Code implementation complete." }
      ]
    },
    {
      title: "Chạy thử & Gỡ lỗi (Debugging)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-debug\" --command \"debug\" --checkpoint 7 --step \"Compiling and testing UI\"",
      agentAction: "Biên dịch và chạy thử kiểm thử lỗi CSS/HTML, ghi nhận kết quả tại `docs/debug/FEAT-015_debug.md`.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-debug\" --command \"debug\" --checkpoint 7 --step \"Compiling and testing UI\"" },
        { type: "success", text: "Linter check: PASS. All tags valid." },
        { type: "output", text: "Saved diagnostics: docs/debug/FEAT-015_debug.md (Status: PASS)." }
      ]
    },
    {
      title: "Nghiệm thu (Verification)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"debug-to-verify\" --command \"verify\" --checkpoint 9 --step \"Final compliance check\" && python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint \"exactly 9\"",
      agentAction: "Chạy kiểm soát tuân thủ thiết kế kỹ thuật, chạy thử Simulator đầy đủ, tạo file nghiệm thu chất lượng `docs/verification/FEAT-015_verify.md`.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"debug-to-verify\" --command \"verify\" --checkpoint 9 --step \"Final compliance check\"" },
        { type: "success", text: "Compliance check: 100% matched blueprint." },
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint \"exactly 9\"" },
        { type: "success", text: "Validation passed. System unlocked for Release." }
      ]
    },
    {
      title: "Phát hành (Release)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-release\" --command \"release\" --checkpoint 10 --step \"Executing release sync\"",
      agentAction: "Đóng gói, bump version lên 5.1.3, cập nhật changelog, push code lên GitLab và chạy `make publish-github` để đẩy website lên GitHub Pages.",
      gate: "release",
      gateText: "Confirm release version 5.1.3 & push to GitLab/GitHub? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-release\" --command \"release\" --checkpoint 10 --step \"Executing release sync\"" },
        { type: "output", text: "Bumping version to 5.1.3. Updating CHANGELOG.md." },
        { type: "warn", text: "Confirm release version 5.1.3 & push to GitLab/GitHub? [Y/N]" }
      ]
    },
    {
      title: "Hoàn tất Workflow",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 10 --step \"Workflow release successfully completed\"",
      agentAction: "Hoàn tất chu kỳ phát hành, lưu dấu checkpoint 10 và tạm dừng để nạp chu kỳ tiếp theo.",
      gate: "none",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 10 --step \"Workflow release successfully completed\"" },
        { type: "success", text: "Step completed. Checkpoint 10 set to status: completed." },
        { type: "output", text: "==================================================" },
        { type: "output", text: "   AI Engineering Workflow Cycle Complete!  " },
        { type: "output", text: "==================================================" }
      ]
    }
  ],
  feature: [
    {
      title: "Khởi tạo (Initialize)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 2",
      agentAction: "Khởi tạo `.agents/.session.json` ở chế độ Full Access. Quyền chỉnh sửa file và chạy test được bypass phê duyệt.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 2" },
        { type: "success", text: "Session initialized with permission_mode=full_access." }
      ]
    },
    {
      title: "Pha 1: Đặc tả (Specification)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-feature\" --command \"feature\" --checkpoint 5 --step \"Specification Phase\"",
      agentAction: "Viết tệp đặc tả tính năng nhỏ tại `docs/quick/QUICK-007_interactive_docs_website.md`.",
      gate: "approval",
      gateText: "Approve QUICK specification for QUICK-007? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-feature\" --command \"feature\" --checkpoint 5 --step \"Specification Phase\"" },
        { type: "output", text: "Writing docs/quick/QUICK-007_interactive_docs_website.md..." },
        { type: "warn", text: "Approve QUICK specification for QUICK-007? [Y/N]" }
      ]
    },
    {
      title: "Pha 2: Thiết kế (Blueprint)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Blueprint Phase\" && python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/QUICK-007_interactive_docs_website_blueprint.md",
      agentAction: "Tạo tệp thiết kế kiến trúc/code chữ ký tại `docs/designs/QUICK-007_interactive_docs_website_blueprint.md` và đăng ký blueprint.",
      gate: "approval",
      gateText: "Approve Blueprint docs/designs/QUICK-007_interactive_docs_website_blueprint.md? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Blueprint Phase\"" },
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/QUICK-007_interactive_docs_website_blueprint.md" },
        { type: "success", text: "Blueprint docs/designs/QUICK-007_interactive_docs_website_blueprint.md registered." },
        { type: "warn", text: "Approve Blueprint docs/designs/QUICK-007_interactive_docs_website_blueprint.md? [Y/N]" }
      ]
    },
    {
      title: "Pha 3: Viết code & Kiểm thử (Implement)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implementation Phase\"",
      agentAction: "Triển khai code các file giao diện tĩnh (bypass duyệt do chế độ Full Access), tự động chạy linter và unit test.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implementation Phase\"" },
        { type: "output", text: "Bypassing approval gate for file modifications (Full Access Mode)." },
        { type: "output", text: "Creating HTML/CSS/JS files..." },
        { type: "success", text: "Running linter and tests: PASS." }
      ]
    },
    {
      title: "Phát hành (Release)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step \"Feature completed\" --next-skill \"implementation-to-release\" --next-command \"release\"",
      agentAction: "Đóng gói, bump version lên 5.1.3, cập nhật changelog và push code/tag lên GitLab/GitHub.",
      gate: "release",
      gateText: "Confirm release version 5.1.3 & push to GitLab/GitHub? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step \"Feature completed\" --next-skill \"implementation-to-release\" --next-command \"release\"" },
        { type: "output", text: "Preparing release package... Bumping version..." },
        { type: "warn", text: "Confirm release version 5.1.3 & push to GitLab/GitHub? [Y/N]" }
      ]
    }
  ],
  fix: [
    {
      title: "Khởi tạo (Initialize)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 2",
      agentAction: "Khởi tạo `.agents/.session.json` ở chế độ Full Access để sửa bug nhanh.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 2" },
        { type: "success", text: "Session initialized with permission_mode=full_access." }
      ]
    },
    {
      title: "Pha 1: Đặc tả lỗi (Specification)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-fix\" --command \"fix\" --checkpoint 5 --step \"Specification Phase\"",
      agentAction: "Tìm hiểu nguyên nhân lỗi và ghi nhận tệp đặc tả sửa lỗi tại `docs/issues/FIX-012_auto_sync_conversation_id.md`.",
      gate: "approval",
      gateText: "Approve QUICK specification for FIX-012? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-fix\" --command \"fix\" --checkpoint 5 --step \"Specification Phase\"" },
        { type: "output", text: "Writing docs/issues/FIX-012_auto_sync_conversation_id.md..." },
        { type: "warn", text: "Approve QUICK specification for FIX-012? [Y/N]" }
      ]
    },
    {
      title: "Pha 2: Thiết kế sửa lỗi (Blueprint)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Blueprint Phase\" && python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FIX-012_auto_sync_conversation_id_blueprint.md",
      agentAction: "Tạo tệp thiết kế/code chữ ký tại `docs/designs/FIX-012_auto_sync_conversation_id_blueprint.md` và đăng ký blueprint.",
      gate: "approval",
      gateText: "Approve Blueprint docs/designs/FIX-012_auto_sync_conversation_id_blueprint.md? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Blueprint Phase\"" },
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FIX-012_auto_sync_conversation_id_blueprint.md" },
        { type: "success", text: "Blueprint docs/designs/FIX-012_auto_sync_conversation_id_blueprint.md registered." },
        { type: "warn", text: "Approve Blueprint docs/designs/FIX-012_auto_sync_conversation_id_blueprint.md? [Y/N]" }
      ]
    },
    {
      title: "Pha 3: Sửa code & Kiểm thử (Implement)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implementation Phase\"",
      agentAction: "Sửa đổi hàm `update_context_health` trong `workflow_runtime.py` (bypass duyệt). Chạy thử nghiệm unit test `test_runtime.py`.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implementation Phase\"" },
        { type: "output", text: "Bypassing approval gate for file modifications (Full Access Mode)." },
        { type: "output", text: "Modifying skills/workflow-runtime/scripts/workflow_runtime.py..." },
        { type: "success", text: "Running pytest: 1 passed. PASS." }
      ]
    },
    {
      title: "Phát hành (Release)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step \"Fix completed\" --next-skill \"implementation-to-release\" --next-command \"release\"",
      agentAction: "Chuẩn bị gói release, bump version lên 5.1.3, cập nhật changelog, push code lên GitLab/GitHub.",
      gate: "release",
      gateText: "Confirm release version 5.1.3 & push to GitLab/GitHub? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step \"Fix completed\" --next-skill \"implementation-to-release\" --next-command \"release\"" },
        { type: "output", text: "Preparing release package... Bumping version..." },
        { type: "warn", text: "Confirm release version 5.1.3 & push to GitLab/GitHub? [Y/N]" }
      ]
    }
  ],
  orchestrated: [
    {
      title: "Khởi tạo (Initialize)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 1",
      agentAction: "Khởi tạo phiên làm việc với phân quyền Sandbox.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 1" },
        { type: "success", text: "Session initialized with permission_mode=sandbox." }
      ]
    },
    {
      title: "Khảo sát ý tưởng (Brainstorm)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming\" --command \"brainstorm\" --checkpoint 3 --step \"Orchestrating Brainstorming\"",
      agentAction: "Khởi tạo pha Brainstorming. Điều phối 2 Agent phân tích (UX Analyst và Security Analyst) chạy song song thu thập ý kiến trước khi tổng hợp tài liệu đặc tả.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming\" --command \"brainstorm\" --checkpoint 3 --step \"Orchestrating Brainstorming\"" },
        { type: "output", text: "Spawning Read-Only Analysis Agents: [UX_Analyst, Security_Analyst]" },
        { type: "success", text: "UX_Analyst completed: UX recommendations added." },
        { type: "success", text: "Security_Analyst completed: Security recommendations added." },
        { type: "output", text: "Generating canonical brainstorming specification docs/brainstorming/FEAT-020_multi_agent_analysis.md." }
      ]
    },
    {
      title: "Lập kế hoạch (Planning)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming-to-plan\" --command \"plan\" --checkpoint 4 --step \"Creating plan with Architect Agent\"",
      agentAction: "Khởi tạo pha lập kế hoạch. Triển khai Agent Architect phân tích rủi ro và các tệp tin liên quan trước khi ghi nhận Kế hoạch thực hiện.",
      gate: "approval",
      gateText: "Approve Implementation Plan for FEAT-020? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming-to-plan\" --command \"plan\" --checkpoint 4 --step \"Creating plan with Architect Agent\"" },
        { type: "output", text: "Spawning Read-Only Analysis Agent: [Architect_Agent]" },
        { type: "success", text: "Architect_Agent completed: Risk assessment & lock verification done." },
        { type: "output", text: "Creating docs/plans/FEAT-020_multi_agent_analysis_plan.md." },
        { type: "warn", text: "Approve Implementation Plan for FEAT-020? [Y/N]" }
      ]
    },
    {
      title: "Thiết kế kỹ thuật (Blueprint)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"plan-to-blueprint\" --command \"blueprint\" --checkpoint 5 --step \"Drafting blueprint\" && python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-020_multi_agent_analysis_blueprint.md",
      agentAction: "Tạo Thiết kế kỹ thuật chi tiết. Đăng ký blueprint lên CLI.",
      gate: "approval",
      gateText: "Approve Blueprint docs/designs/FEAT-020_multi_agent_analysis_blueprint.md? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"plan-to-blueprint\" --command \"blueprint\" --checkpoint 5 --step \"Drafting blueprint\"" },
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-020_multi_agent_analysis_blueprint.md" },
        { type: "success", text: "Blueprint docs/designs/FEAT-020_multi_agent_analysis_blueprint.md registered." },
        { type: "warn", text: "Approve Blueprint docs/designs/FEAT-020_multi_agent_analysis_blueprint.md? [Y/N]" }
      ]
    },
    {
      title: "Song song viết code (Parallel Implementation)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py execution mode --mode parallel",
      agentAction: "Chọn chế độ thực thi song song (Parallel Mode) cho Pha Viết code. Hệ sinh thái kiểm tra xung đột phân luồng ghi và khóa file lock trước khi thực thi.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py execution mode --mode parallel" },
        { type: "output", text: "Execution Mode set to: PARALLEL." },
        { type: "output", text: "Topological groups: Group 1: [rules, runtime], Group 2: [webview, docs], Group 3: [tests]." },
        { type: "output", text: "Spawning worker agents for Group 1..." },
        { type: "success", text: "Workers for Group 1 completed successfully." }
      ]
    },
    {
      title: "Phát hành (Release)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step \"Feature completed\" --next-skill \"implementation-to-release\" --next-command \"release\"",
      agentAction: "Đóng gói release, bump version lên 5.1.3, cập nhật changelog và push code lên GitHub.",
      gate: "release",
      gateText: "Confirm release version 5.1.3 & push to GitHub? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step \"Feature completed\" --next-skill \"implementation-to-release\" --next-command \"release\"" },
        { type: "output", text: "Preparing release package... Bumping version..." },
        { type: "warn", text: "Confirm release version 5.1.3 & push to GitHub? [Y/N]" }
      ]
    }
  ]
};

function initSimulator() {
  const workflowSelect = document.querySelector("#workflowSelect");
  const simStepTitle = document.querySelector("#simStepTitle");
  const simAgentAction = document.querySelector("#simAgentAction");
  const simCliCommand = document.querySelector("#simCliCommand");
  const simProgress = document.querySelector("#simProgress");
  
  const btnRunCli = document.querySelector("#btnRunCli");
  const btnApprove = document.querySelector("#btnApprove");
  const btnReset = document.querySelector("#btnReset");
  const terminalBody = document.querySelector("#terminalBody");

  let isCliExecuted = false;

  function updateUi() {
    const steps = simStepsData[simCurrentWorkflow];
    const currentStep = steps[simCurrentStepIndex];

    // Update Text labels
    simStepTitle.textContent = `Bước ${simCurrentStepIndex + 1}: ${currentStep.title}`;
    simAgentAction.innerHTML = `<strong>Hành động của Agent:</strong> ${currentStep.agentAction}`;
    simCliCommand.textContent = currentStep.cli;
    simProgress.textContent = `Bước ${simCurrentStepIndex + 1} / ${steps.length}`;

    // Manage button states
    if (!isCliExecuted) {
      btnRunCli.style.display = "block";
      btnApprove.style.display = "none";
      btnRunCli.textContent = "Chạy CLI";
    } else {
      btnRunCli.style.display = "none";
      
      if (currentStep.gate === "proceed") {
        btnApprove.style.display = "block";
        btnApprove.textContent = "Tiếp tục (Bypass)";
        btnApprove.style.background = "var(--blue)";
      } else if (currentStep.gate === "approval") {
        btnApprove.style.display = "block";
        btnApprove.textContent = "Phê duyệt [Y]";
        btnApprove.style.background = "var(--green)";
      } else if (currentStep.gate === "release") {
        btnApprove.style.display = "block";
        btnApprove.textContent = "Phát hành [Y]";
        btnApprove.style.background = "var(--pink)";
      } else {
        btnApprove.style.display = "block";
        btnApprove.textContent = "Hoàn thành";
        btnApprove.style.background = "var(--cyan)";
      }
    }
  }

  function resetSimulator() {
    simCurrentStepIndex = 0;
    isCliExecuted = false;
    terminalBody.innerHTML = `<span class="terminal-prompt">Guest@AI-Workflow:~$</span> <span class="terminal-cmd"># Sẵn sàng giả lập quy trình ${simCurrentWorkflow.toUpperCase()}</span>\n`;
    updateUi();
  }

  // Handle Switch Workflow Select
  workflowSelect.addEventListener("change", (e) => {
    simCurrentWorkflow = e.target.value;
    resetSimulator();
  });

  // Handle Run CLI button click
  btnRunCli.addEventListener("click", () => {
    const steps = simStepsData[simCurrentWorkflow];
    const currentStep = steps[simCurrentStepIndex];

    // Append CLI command and its simulated outputs to Terminal screen
    currentStep.terminal.forEach(line => {
      const div = document.createElement("div");
      if (line.type === "prompt") {
        div.innerHTML = `<span class="terminal-prompt">Guest@AI-Workflow:~$</span> <span class="terminal-cmd">${line.text}</span>`;
      } else if (line.type === "success") {
        div.className = "terminal-success";
        div.textContent = line.text;
      } else if (line.type === "warn") {
        div.className = "terminal-warn";
        div.textContent = line.text;
      } else if (line.type === "error") {
        div.className = "terminal-error";
        div.textContent = line.text;
      } else {
        div.className = "terminal-output";
        div.textContent = line.text;
      }
      terminalBody.appendChild(div);
    });

    // Auto scroll to bottom of Terminal
    setTimeout(() => {
      terminalBody.scrollTop = terminalBody.scrollHeight;
    }, 50);

    isCliExecuted = true;
    updateUi();
  });

  // Handle Approve / Proceed button click
  btnApprove.addEventListener("click", () => {
    const steps = simStepsData[simCurrentWorkflow];
    const currentStep = steps[simCurrentStepIndex];

    // If there was an approval gate, print the user response "Y" to the terminal
    if (currentStep.gate === "approval" || currentStep.gate === "release") {
      const userDiv = document.createElement("div");
      userDiv.innerHTML = `<span class="terminal-prompt">User Input:</span> <span class="terminal-cmd" style="color: var(--green);">Y</span>`;
      terminalBody.appendChild(userDiv);
      
      const resDiv = document.createElement("div");
      resDiv.className = "terminal-success";
      resDiv.textContent = "Proceeding gate approved by user.";
      terminalBody.appendChild(resDiv);
    }

    // Go to next step or complete
    if (simCurrentStepIndex < steps.length - 1) {
      simCurrentStepIndex++;
      isCliExecuted = false;
      updateUi();
    } else {
      // Completed, loop back to reset
      resetSimulator();
    }

    setTimeout(() => {
      terminalBody.scrollTop = terminalBody.scrollHeight;
    }, 50);
  });

  // Handle Reset button click
  btnReset.addEventListener("click", () => {
    resetSimulator();
  });

  // Initial Boot
  resetSimulator();
}
