<script>
  import { onMount, onDestroy } from "svelte";
  import DAGViewer from "./components/DAGViewer.svelte";
  import AgentMonitor from "./components/AgentMonitor.svelte";
  import LogStreamer from "./components/LogStreamer.svelte";
  import ResourceGovernor from "./components/ResourceGovernor.svelte";

  let projects = [];
  let selectedProject = null;
  let connectionStatus = "disconnected";
  let noticeMessage = "";

  // Active state telemetry
  let tasks = [];
  let agents = [];
  let logs = [];
  let cpuUsage = 0;
  let ramUsage = 0;
  let currentTokens = 0;
  let totalTokensLimit = 2000000;

  // Form input to register project
  let newProjName = "";
  let newProjPath = "";
  let newProjPort = 8085;

  onMount(async () => {
    await loadProjects();

    // Setup listener globally for telemetry updates
    if (window.runtime) {
      window.runtime.EventsOn("status:*", (data) => {
        console.log("Status update:", data);
      });
    }
  });

  onDestroy(() => {
    if (selectedProject) {
      disconnectFromProject(selectedProject.id);
    }
  });

  async function loadProjects() {
    if (window.go && window.go.main && window.go.main.App) {
      try {
        projects = await window.go.main.App.GetProjects();
      } catch (err) {
        console.error("Lỗi lấy danh sách dự án:", err);
      }
    }
  }

  async function registerProject() {
    if (!newProjName || !newProjPath) return;
    if (window.go && window.go.main && window.go.main.App) {
      try {
        const p = await window.go.main.App.RegisterProject(newProjName, newProjPath, newProjPort);
        projects = [...projects, p];
        newProjName = "";
        newProjPath = "";
      } catch (err) {
        noticeMessage = "Project registration failed: " + err;
      }
    }
  }

  async function deleteProject(id) {
    if (window.go && window.go.main && window.go.main.App) {
      try {
        await window.go.main.App.DeleteProject(id);
        if (selectedProject && selectedProject.id === id) {
          selectedProject = null;
        }
        await loadProjects();
      } catch (err) {
        console.error(err);
      }
    }
  }

  async function selectProject(project) {
    if (selectedProject) {
      disconnectFromProject(selectedProject.id);
    }
    selectedProject = project;

    // Reset state telemetry
    tasks = [];
    agents = [];
    logs = [];
    cpuUsage = 0;
    ramUsage = 0;
    currentTokens = 0;

    await connectToProject(project.id, project.port);
  }

  async function connectToProject(id, port) {
    if (window.go && window.go.main && window.go.main.App) {
      await window.go.main.App.ConnectProject(id, port);

      // Bind Wails telemetry events
      window.runtime.EventsOn("telemetry:" + id, (payload) => {
        try {
          const data = typeof payload === "string" ? JSON.parse(payload) : payload;
          tasks = data.tasks || [];
          agents = data.agents || [];
          cpuUsage = data.cpu || 0;
          ramUsage = data.ram || 0;
          currentTokens = data.tokens_used || 0;

          if (data.log) {
            logs = [...logs, data.log];
          }
        } catch (e) {
          console.error("Lỗi parse telemetry:", e);
        }
      });

      window.runtime.EventsOn("status:" + id, (state) => {
        connectionStatus = state.status || "disconnected";
      });
    }
  }

  function disconnectFromProject(id) {
    if (window.go && window.go.main && window.go.main.App) {
      window.go.main.App.DisconnectProject(id);
      window.runtime.EventsOff("telemetry:" + id);
      window.runtime.EventsOff("status:" + id);
      connectionStatus = "disconnected";
    }
  }

  async function handleStart() {
    if (!selectedProject) return;
    if (window.go && window.go.main && window.go.main.App) {
      try {
        const success = await window.go.main.App.StartOrchestrator(selectedProject.path, "brainstorming", "brainstorm");
        if (success) {
          noticeMessage = "Resident Orchestrator started successfully.";
        }
      } catch (err) {
        noticeMessage = "Start failed: " + err;
      }
    }
  }

  async function handleStop() {
    if (!selectedProject) return;
    if (window.go && window.go.main && window.go.main.App) {
      try {
        await window.go.main.App.StopOrchestrator(selectedProject.path);
        noticeMessage = "Stop request sent to Resident Orchestrator.";
      } catch (err) {
        noticeMessage = "Stop failed: " + err;
      }
    }
  }
</script>

<div class="flex h-screen bg-slate-950 text-slate-100 font-sans">
  <!-- Sidebar Project Registry -->
  <div class="w-80 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-4">
    <div class="flex flex-col gap-1 border-b border-slate-800 pb-4">
      <h1 class="text-lg font-black tracking-tight text-white">AIWF Control Center</h1>
      <p class="text-xs text-slate-400">Thiết bị quản trị & Giám sát Runtime</p>
    </div>

    <!-- Registry Register Form -->
    <div class="bg-slate-950/60 p-3 rounded-md border border-slate-800 flex flex-col gap-3">
      <h2 class="text-xs font-bold text-slate-300">Đăng ký dự án mới</h2>
      <input type="text" placeholder="Tên dự án" bind:value={newProjName} class="w-full text-xs bg-slate-900 border border-slate-700 rounded px-2 py-1 focus:outline-none" />
      <input type="text" placeholder="Đường dẫn path" bind:value={newProjPath} class="w-full text-xs bg-slate-900 border border-slate-700 rounded px-2 py-1 focus:outline-none" />
      <input type="number" placeholder="Port WebSocket (vd: 8085)" bind:value={newProjPort} class="w-full text-xs bg-slate-900 border border-slate-700 rounded px-2 py-1 focus:outline-none" />
      <button on:click={registerProject} class="w-full bg-emerald-600 hover:bg-emerald-500 text-xs font-bold py-1.5 rounded transition">Thêm dự án</button>
    </div>

    <!-- Projects List -->
    <div class="flex-1 overflow-y-auto flex flex-col gap-2">
      <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Danh sách dự án</h3>
      {#each projects as project}
        <div
          class="p-3 rounded-md border cursor-pointer flex justify-between items-center transition {selectedProject && selectedProject.id === project.id ? 'bg-emerald-950/20 border-emerald-500 text-emerald-300' : 'bg-slate-850 border-slate-800 hover:bg-slate-800 text-slate-300'}"
          on:click={() => selectProject(project)}
        >
          <div class="flex flex-col">
            <span class="text-sm font-bold">{project.name}</span>
            <span class="text-[10px] text-slate-500 truncate max-w-[160px]">{project.path}</span>
          </div>
          <button
            on:click|stopPropagation={() => deleteProject(project.id)}
            class="text-[10px] text-red-500 hover:text-red-400 bg-red-950/20 px-2 py-0.5 rounded border border-red-900/50"
          >
            Xóa
          </button>
        </div>
      {/each}
    </div>
  </div>

  <!-- Main Telemetry Cockpit -->
  <div class="flex-1 p-6 flex flex-col gap-6 overflow-y-auto bg-gradient-to-br from-slate-950 to-slate-900">
    {#if !selectedProject}
      <div class="flex-1 flex flex-col items-center justify-center text-center">
        <div class="w-16 h-16 bg-slate-900 border border-slate-800 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <h2 class="text-lg font-bold text-slate-300">Vui lòng chọn một dự án</h2>
        <p class="text-sm text-slate-500 mt-1 max-w-sm">Chọn một dự án từ danh sách bên trái hoặc đăng ký dự án mới để bắt đầu giám sát trạng thái runtime.</p>
      </div>
    {:else}
      <!-- Cockpit Header & Controls -->
      <div class="flex justify-between items-center border-b border-slate-800 pb-4">
        <div class="flex flex-col">
          <h2 class="text-2xl font-bold tracking-tight text-white">{selectedProject.name}</h2>
          <div class="flex items-center gap-2 mt-1">
            <span class="w-2.5 h-2.5 rounded-full {connectionStatus === 'connected' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}"></span>
            <span class="text-xs text-slate-400 font-mono">Status: {connectionStatus.toUpperCase()} (Port {selectedProject.port})</span>
          </div>
        </div>

      <div class="flex gap-2">
          <button
            on:click={handleStart}
            class="bg-emerald-600 hover:bg-emerald-500 text-xs font-bold px-4 py-2 rounded-md transition shadow-md shadow-emerald-950/20"
          >
            Khởi động
          </button>
          <button
            on:click={handleStop}
            class="bg-red-600 hover:bg-red-500 text-xs font-bold px-4 py-2 rounded-md transition shadow-md shadow-red-950/20"
          >
            Tạm dừng
          </button>
      </div>
      {#if noticeMessage}
        <div class="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-300">
          {noticeMessage}
        </div>
      {/if}
    </div>

      <!-- Resource Charts component -->
      <ResourceGovernor {cpuUsage} {ramUsage} {currentTokens} {totalTokensLimit} />

      <!-- Active DAG Canvas -->
      <DAGViewer {tasks} />

      <!-- Columns split for logs and active agent tree -->
      <div class="grid grid-cols-2 gap-6">
        <AgentMonitor {agents} />
        <LogStreamer bind:logs />
      </div>
    {/if}
  </div>
</div>
