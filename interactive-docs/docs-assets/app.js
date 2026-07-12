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
        "overview": "Tổng quan AIWF Orchestrated SDLC",
        "workflows": "Workflow, Orchestrator và Multi-Agent Flows",
        "skills": "Thư mục Skills chi tiết (Skills Directory)",
        "runtime": "Runtime, State và Knowledge Operations",
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
      title: "Khởi tạo nhẹ (Initialize)",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 1 --non-interactive",
      agentAction: "Nạp guardrails, đọc split-state cache, kiểm tra Git ở mức tối thiểu và thiết lập phiên sandbox. Init không quét toàn bộ source, không gọi RAG nặng và không tự release.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py init --permission 1 --non-interactive" },
        { type: "success", text: "Session initialized with permission_mode=sandbox." },
        { type: "output", text: "Split-state ready under .agents/state/." }
      ]
    },
    {
      title: "Đồng bộ Project Memory",
      cli: "python runtime/scripts/project_memory/cli.py update",
      agentAction: "Cập nhật Project Memory bằng Git diff, sau đó Knowledge Runtime/provider layer chịu trách nhiệm đồng bộ các bề mặt tri thức liên quan.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python runtime/scripts/project_memory/cli.py update" },
        { type: "output", text: "Detection method: git-diff." },
        { type: "success", text: "Project memory updated successfully." }
      ]
    },
    {
      title: "Skill Suggestion Gate",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py classify --request \"user request\"",
      agentAction: "Yêu cầu tự nhiên được phân loại trước khi làm việc. Hệ thống đề xuất quick-fix, quick-feature, brainstorming, blueprint-to-implementation, debug, verify hoặc release theo ngữ cảnh.",
      gate: "approval",
      gateText: "Continue with recommended workflow? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py classify --request \"update docs\"" },
        { type: "output", text: "Classification: quick-feature." },
        { type: "warn", text: "Confirm to continue? [Y/N]" }
      ]
    },
    {
      title: "Brainstorming / Discovery",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming\" --command \"brainstorm\" --checkpoint 3 --step \"Discover requirements\"",
      agentAction: "Pha khám phá chỉ tạo tài liệu yêu cầu trong docs/brainstorming/. Không viết code, không đổi kiến trúc đã đóng băng.",
      gate: "approval",
      gateText: "Approve brainstorming output? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming\" --command \"brainstorm\" --checkpoint 3 --step \"Discover requirements\"" },
        { type: "output", text: "Writing docs/brainstorming/FEAT-XXX_slug.md." },
        { type: "warn", text: "Approve brainstorming output? [Y/N]" }
      ]
    },
    {
      title: "Planning",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming-to-plan\" --command \"plan\" --checkpoint 4 --step \"Create plan\"",
      agentAction: "Kế hoạch mô tả scope, deliverables, rủi ro và cách nghiệm thu. Plan không định nghĩa class, API, database schema hoặc pseudo-code.",
      gate: "approval",
      gateText: "Approve implementation plan? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"brainstorming-to-plan\" --command \"plan\" --checkpoint 4 --step \"Create plan\"" },
        { type: "success", text: "Plan synchronized into docs/plans/." },
        { type: "warn", text: "Approve implementation plan? [Y/N]" }
      ]
    },
    {
      title: "Blueprint Contract",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-XXX_slug_blueprint.md",
      agentAction: "Blueprint là hợp đồng kỹ thuật duy nhất cho code change: file-by-file, API contracts, checklist và test strategy. Chưa approve blueprint thì không được implement.",
      gate: "approval",
      gateText: "Approve blueprint? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-XXX_slug_blueprint.md" },
        { type: "success", text: "Blueprint registered." },
        { type: "warn", text: "Approve blueprint? [Y/N]" }
      ]
    },
    {
      title: "Implementation từ Blueprint",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"blueprint-to-implementation\" --command \"implement\" --checkpoint 6 --step \"Implement approved blueprint\"",
      agentAction: "Chỉ sửa các file có trong blueprint đã duyệt. Các thay đổi ngoài scope hoặc refactor không liên quan bị chặn.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"blueprint-to-implementation\" --command \"implement\" --checkpoint 6 --step \"Implement approved blueprint\"" },
        { type: "output", text: "Applying scoped file changes from blueprint." },
        { type: "success", text: "Implementation phase complete." }
      ]
    },
    {
      title: "Debug và Validation",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-debug\" --command \"debug\" --checkpoint 7 --step \"Run validation\"",
      agentAction: "Chạy build/lint/typecheck/tests theo stack phát hiện được. Chỉ tự sửa lỗi nằm trong file thuộc scope task hiện tại.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-debug\" --command \"debug\" --checkpoint 7 --step \"Run validation\"" },
        { type: "success", text: "Build/Lint/Tests: PASS or Not Configured." }
      ]
    },
    {
      title: "Verify Quality Gate",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"debug-to-verify\" --command \"verify\" --checkpoint 9 --step \"Final quality gate\"",
      agentAction: "Đối chiếu implementation với blueprint và acceptance criteria. PASS ở verify mới đủ điều kiện đề xuất release.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"debug-to-verify\" --command \"verify\" --checkpoint 9 --step \"Final quality gate\"" },
        { type: "success", text: "Verification report: PASS." }
      ]
    },
    {
      title: "Release rõ ràng",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-release\" --command \"release\" --checkpoint 10 --step \"Release gate\"",
      agentAction: "Release không bao giờ tự động. Version bump, changelog, commit, tag, merge và push đều cần yêu cầu release và approval riêng.",
      gate: "release",
      gateText: "Confirm release actions? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-release\" --command \"release\" --checkpoint 10 --step \"Release gate\"" },
        { type: "warn", text: "Confirm version/changelog/git tag/push actions? [Y/N]" }
      ]
    }
  ],
  feature: [
    {
      title: "Validate checkpoint 2",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint \"exactly 2\"",
      agentAction: "Quick Feature chỉ bắt đầu sau khi init và memory context sẵn sàng. Nếu checkpoint sai, workflow dừng thay vì viết spec bừa.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint \"exactly 2\"" },
        { type: "success", text: "Validation passed." }
      ]
    },
    {
      title: "Pha 1: QUICK Spec",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-feature\" --command \"feature\" --checkpoint 5 --step \"Create QUICK spec\"",
      agentAction: "Tạo docs/quick/QUICK-XXX_slug.md với goal, scope boundary, dependency contract, error matrix và acceptance criteria.",
      gate: "approval",
      gateText: "Approve QUICK specification? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-feature\" --command \"feature\" --checkpoint 5 --step \"Create QUICK spec\"" },
        { type: "output", text: "Writing docs/quick/QUICK-XXX_slug.md." },
        { type: "warn", text: "Approve QUICK specification? [Y/N]" }
      ]
    },
    {
      title: "Pha 2: Blueprint",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/QUICK-XXX_slug_blueprint.md",
      agentAction: "Tạo blueprint file-by-file. Blueprint phải nêu rõ các file được sửa, checklist implementation và test plan trước khi code được phép thay đổi.",
      gate: "approval",
      gateText: "Approve Blueprint? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/QUICK-XXX_slug_blueprint.md" },
        { type: "success", text: "Blueprint registered." },
        { type: "warn", text: "Approve Blueprint? [Y/N]" }
      ]
    },
    {
      title: "Pre-implementation Gate",
      cli: "git branch --show-current && git status --short",
      agentAction: "Trước khi sửa file, agent báo branch, dirty tree và danh sách file dự kiến chỉnh. Người dùng xác nhận rồi mới implement.",
      gate: "approval",
      gateText: "Proceed with implementation? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ git branch --show-current" },
        { type: "output", text: "feature/QUICK-XXX-slug or current approved branch" },
        { type: "prompt", text: "$ git status --short" },
        { type: "warn", text: "Proceed with implementation? [Y/N]" }
      ]
    },
    {
      title: "Pha 3: Implement scoped files",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implementation Phase\"",
      agentAction: "Chỉ sửa file đã liệt kê trong blueprint. Ví dụ với docs site: index.html, app.js, skills-data.js và CSS nếu có overflow.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implementation Phase\"" },
        { type: "output", text: "Applying approved docs-site changes only." },
        { type: "success", text: "Scoped implementation complete." }
      ]
    },
    {
      title: "Static verification",
      cli: "node --check interactive-docs/docs-assets/app.js",
      agentAction: "Kiểm tra cú pháp JS, mở trang tĩnh, thử tab/search/simulator và đảm bảo không có absolute local path trong docs site.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ node --check interactive-docs/docs-assets/app.js" },
        { type: "success", text: "JavaScript syntax: PASS." },
        { type: "success", text: "Tabs/search/simulator: verified." }
      ]
    }
  ],
  fix: [
    {
      title: "Classify localized bug",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py classify --request \"bug description\"",
      agentAction: "Bug nhỏ, cục bộ được route vào quick-fix. Bug rộng hoặc ảnh hưởng kiến trúc phải đi brainstorming/standard workflow.",
      gate: "approval",
      gateText: "Continue with quick-fix? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py classify --request \"broken validation\"" },
        { type: "output", text: "Classification: quick-fix." },
        { type: "warn", text: "Continue with quick-fix? [Y/N]" }
      ]
    },
    {
      title: "FIX Spec",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-fix\" --command \"fix\" --checkpoint 5 --step \"Create FIX spec\"",
      agentAction: "Ghi nhận root cause, phạm vi sửa lỗi, failure behavior và acceptance criteria trong docs/issues/FIX-XXX_slug.md.",
      gate: "approval",
      gateText: "Approve FIX specification? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"quick-fix\" --command \"fix\" --checkpoint 5 --step \"Create FIX spec\"" },
        { type: "output", text: "Writing docs/issues/FIX-XXX_slug.md." },
        { type: "warn", text: "Approve FIX specification? [Y/N]" }
      ]
    },
    {
      title: "FIX Blueprint",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FIX-XXX_slug_blueprint.md",
      agentAction: "Blueprint nêu chính xác file nào sửa, hành vi nào thay đổi và test nào chứng minh lỗi đã hết.",
      gate: "approval",
      gateText: "Approve FIX blueprint? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FIX-XXX_slug_blueprint.md" },
        { type: "success", text: "FIX blueprint registered." },
        { type: "warn", text: "Approve FIX blueprint? [Y/N]" }
      ]
    },
    {
      title: "Scoped fix implementation",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implement FIX blueprint\"",
      agentAction: "Chỉ sửa lỗi trong write set đã duyệt. Không refactor lan rộng, không sửa module không liên quan.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py step --step \"Implement FIX blueprint\"" },
        { type: "output", text: "Applying localized fix." },
        { type: "success", text: "Fix implementation complete." }
      ]
    },
    {
      title: "Regression validation",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-debug\" --command \"debug\" --checkpoint 7 --step \"Run fix validation\"",
      agentAction: "Chạy test liên quan và regression checks. Nếu fail ngoài scope, dừng và báo thay vì sửa lan rộng.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"implementation-to-debug\" --command \"debug\" --checkpoint 7 --step \"Run fix validation\"" },
        { type: "success", text: "Targeted tests: PASS." }
      ]
    }
  ],
  orchestrated: [
    {
      title: "Orchestrator entrypoint",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"orchestrator\" --command \"orchestrate\" --step \"Route request\"",
      agentAction: "Orchestrator là điểm vào điều phối. Worker skills không tự spawn worker khác và không tự sở hữu session state toàn cục.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py start --skill \"orchestrator\" --command \"orchestrate\" --step \"Route request\"" },
        { type: "success", text: "Orchestrator owns workflow routing." }
      ]
    },
    {
      title: "Memory/RAG first classification",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py knowledge search --query \"request context\"",
      agentAction: "Orchestrator đọc Project Memory, docs và targeted RAG trước khi đề xuất workflow. Không scan toàn repo như bước đầu.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py knowledge search --query \"request context\"" },
        { type: "output", text: "Relevant memory and artifacts loaded." }
      ]
    },
    {
      title: "Read-only analysis subagents",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py analysis-agent create --role RiskAnalyst",
      agentAction: "Trong discovery, planning, blueprint, verify và release, subagents chỉ phân tích read-only. Họ không sửa source, không commit, không đổi state chính.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py analysis-agent create --role RiskAnalyst" },
        { type: "output", text: "Analysis agent scope: read-only." },
        { type: "success", text: "Structured recommendation returned." }
      ]
    },
    {
      title: "Blueprint defines read/write sets",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-XXX_slug_blueprint.md",
      agentAction: "Blueprint phải chỉ rõ file-by-file responsibilities, read set, write set và checklist. Parallel implementation không được bắt đầu trước khi blueprint được duyệt.",
      gate: "approval",
      gateText: "Approve orchestrated blueprint? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/designs/FEAT-XXX_slug_blueprint.md" },
        { type: "success", text: "Blueprint registered with implementation contract." },
        { type: "warn", text: "Approve orchestrated blueprint? [Y/N]" }
      ]
    },
    {
      title: "Execution mode choice",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py execution mode --mode sequential",
      agentAction: "Người dùng chỉ chọn Parallel/Sequential khi bước implementation sẵn sàng. Không hỏi mode ở discovery, planning hoặc blueprinting.",
      gate: "approval",
      gateText: "Choose execution mode? [Parallel/Sequential/Re-split/Cancel]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py execution mode --mode sequential" },
        { type: "warn", text: "Choose execution mode before implementation starts." }
      ]
    },
    {
      title: "Worker agents with file locks",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py lock acquire --path interactive-docs/index.html",
      agentAction: "Worker agents chỉ chạy ở implementation, mỗi worker có write set không chồng lấn và phải acquire file lock trước khi sửa file.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py lock acquire --path interactive-docs/index.html" },
        { type: "output", text: "Lock acquired for assigned write set." },
        { type: "success", text: "Worker completed scoped task." }
      ]
    },
    {
      title: "Aggregate, debug, verify",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py verify --checkpoint 9",
      agentAction: "Orchestrator tổng hợp worker output, sau đó debug/verify chạy theo gates tuần tự để đảm bảo compliance với blueprint.",
      gate: "proceed",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py verify --checkpoint 9" },
        { type: "success", text: "Worker outputs aggregated and verified." }
      ]
    },
    {
      title: "Explicit release only",
      cli: "python skills/workflow-runtime/scripts/workflow_runtime.py release --help",
      agentAction: "Dù orchestrated hay sequential, release vẫn cần yêu cầu rõ ràng. Commit, tag, push, changelog và version bump không tự động xảy ra.",
      gate: "release",
      gateText: "Confirm release actions? [Y/N]",
      terminal: [
        { type: "prompt", text: "$ python skills/workflow-runtime/scripts/workflow_runtime.py release --help" },
        { type: "warn", text: "Release requires explicit user approval." }
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
