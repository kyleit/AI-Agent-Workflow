<script>
  import { onMount, onDestroy } from 'svelte';
  import Sidebar from './lib/Sidebar.svelte';
  import TitleBar from './lib/TitleBar.svelte';
  import Dashboard from './lib/Dashboard.svelte';
  import ProjectsTab from './lib/ProjectsTab.svelte';
  import DaemonsTab from './lib/DaemonsTab.svelte';
  import MemoryTab from './lib/MemoryTab.svelte';
  import SystemTab from './lib/SystemTab.svelte';
  import DocsWebviewTab from './lib/DocsWebviewTab.svelte';
  import SkillLauncher from './lib/SkillLauncher.svelte';
  import ApprovalModal from './lib/ApprovalModal.svelte';
  import LockedState from './lib/LockedState.svelte';

  // Import Wails APIs
  import {
    GetProjects,
    GetSelectedProject,
    SelectProject,
    AddProject,
    DeleteProject,
    SelectProjectFolder,
    ScanProjectFolders,
    GetWorkflowState,
    RunCoordinatorTick,
    SubmitPromptResponse
  } from '../wailsjs/go/main/App';

  let activeTab = 'visualizer';
  let projects = [];
  let selectedProject = null;
  let workflowTimer = null;
  let notice = null;

  let runtimeState = {
    current_skill: 'initialize-workflow',
    current_command: 'init',
    current_step: 'Awaiting project selection...',
    status: 'idle',
    checkpoint: 1
  };

  function showNotice(title, message) {
    notice = {
      title,
      message: String(message || '')
    };
  }

  function closeNotice() {
    notice = null;
  }

  let promptGate = {
    pending: false,
    question: '',
    options: ['Continue', 'Cancel']
  };

  async function loadProjects() {
    try {
      projects = await GetProjects();
      const active = projects.find(p => p.active);
      if (active) {
        selectedProject = active;
        startWorkflowPolling();
      } else {
        selectedProject = null;
        stopWorkflowPolling();
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  }

  async function handleSelectProject(event) {
    const path = event.detail.path;
    try {
      await SelectProject(path);
      await loadProjects();
    } catch (err) {
      showNotice('Project selection failed', err);
    }
  }

  async function handleScanProjects(event) {
    const { onResult, onError } = event.detail;
    try {
      const root = await SelectProjectFolder();
      if (!root) {
        if (onResult) onResult([], '');
        return;
      }
      const candidates = await ScanProjectFolders(root);
      if (onResult) onResult(candidates || [], root);
    } catch (err) {
      if (onError) onError(String(err));
      showNotice('Project scan failed', err);
    }
  }

  async function handleRegisterProject(event) {
    const { name, path } = event.detail;
    try {
      await AddProject(name, path);
      await loadProjects();
    } catch (err) {
      showNotice('Project registration failed', err);
    }
  }

  async function handleDeleteProject(event) {
    const id = event.detail.id;
    try {
      await DeleteProject(id);
      if (selectedProject && projects.find(p => p.id === id)?.path === selectedProject.path) {
        await SelectProject('');
        selectedProject = null;
        stopWorkflowPolling();
      }
      await loadProjects();
    } catch (err) {
      showNotice('Project deletion failed', err);
    }
  }

  async function updateWorkflowState() {
    if (!selectedProject) return;
    try {
      const state = await GetWorkflowState();
      if (state) {
        runtimeState = state;
      }

      // Auto-trigger approval gate when waiting_for_approval is detected
      if (runtimeState.status === 'waiting_for_approval') {
        promptGate = {
          pending: true,
          question: 'Approve this Technical Design Blueprint for implementation?',
          options: ['Continue', 'Cancel']
        };
      } else {
        promptGate.pending = false;
      }
    } catch (err) {
      console.error('Failed to update workflow state:', err);
    }
  }

  function startWorkflowPolling() {
    stopWorkflowPolling();
    updateWorkflowState();
    workflowTimer = setInterval(updateWorkflowState, 3000);
  }

  function stopWorkflowPolling() {
    if (workflowTimer) {
      clearInterval(workflowTimer);
      workflowTimer = null;
    }
  }

  function handleSelectTab(tab) {
    activeTab = tab;
  }

  function handleNavigateToProjects() {
    activeTab = 'projects';
  }

  async function handleRun(event) {
    const promptText = event.detail || event;
    if (!selectedProject) return;
    try {
      runtimeState = {
        current_skill: 'workflow-coordinator',
        current_command: 'tick',
        current_step: 'Running coordinator tick command...',
        status: 'in_progress',
        checkpoint: 1
      };
      await RunCoordinatorTick(promptText);
      await updateWorkflowState();
    } catch (err) {
      showNotice('Workflow execution failed', err);
      await updateWorkflowState();
    }
  }

  async function handlePromptResponse(choice) {
    promptGate.pending = false;
    try {
      await SubmitPromptResponse(choice);
      await updateWorkflowState();
    } catch (err) {
      showNotice('Prompt response failed', err);
    }
  }

  onMount(() => {
    loadProjects();
    const preventContextMenu = (event) => event.preventDefault();
    window.addEventListener('contextmenu', preventContextMenu);
    return () => window.removeEventListener('contextmenu', preventContextMenu);
  });

  onDestroy(() => {
    stopWorkflowPolling();
  });
</script>

<div class="min-h-screen bg-slate-950 text-slate-100 font-sans">
  <!-- Custom TitleBar -->
  <TitleBar />

  <!-- Navigation Sidebar -->
  <Sidebar {activeTab} onSelectTab={handleSelectTab} />

  <!-- Main Content Workspace Area -->
  {#if activeTab === 'docs'}
    <main class="fixed top-8 bottom-0 left-64 right-0 overflow-hidden bg-slate-950">
      <DocsWebviewTab />
    </main>
  {:else}
    <main class="fixed top-8 bottom-0 left-64 right-0 overflow-y-auto app-scrollbar">
      <div class="max-w-7xl mx-auto p-8 space-y-8">
        {#if activeTab === 'visualizer'}
          <div class="space-y-8">
            <div>
              <h2 class="text-xl font-bold text-slate-100 font-mono">AIWF Realtime Visualizer</h2>
              <p class="text-xs text-slate-400 mt-1">Observe and execute the AI Engineering Workflow process (aiwf workflow)</p>
            </div>

            {#if !selectedProject}
              <LockedState featureName="Realtime Visualizer" on:navigateToProjects={handleNavigateToProjects} />
            {:else}
              <Dashboard {runtimeState} />
              <SkillLauncher onRun={handleRun} />
            {/if}
          </div>
        {:else if activeTab === 'projects'}
          <ProjectsTab
            {projects}
            {selectedProject}
            on:scanProjects={handleScanProjects}
            on:registerProject={handleRegisterProject}
            on:selectProject={handleSelectProject}
            on:deleteProject={handleDeleteProject}
          />
        {:else if activeTab === 'daemons'}
          <DaemonsTab {selectedProject} on:refreshProjects={loadProjects} />
        {:else if activeTab === 'memory'}
          <MemoryTab {selectedProject} on:navigateToProjects={handleNavigateToProjects} />
        {:else if activeTab === 'system'}
          <SystemTab {selectedProject} on:navigateToProjects={handleNavigateToProjects} />
        {/if}
      </div>
    </main>
  {/if}

  <!-- Interactive Approval Gate Modal -->
  <ApprovalModal prompt={promptGate} onSelect={handlePromptResponse} />

  {#if notice}
    <div class="fixed inset-0 z-50 flex items-end justify-end bg-slate-950/40 p-6">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="notice-title"
        class="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-5 shadow-2xl"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="space-y-2">
            <h2 id="notice-title" class="text-sm font-bold text-slate-100">{notice.title}</h2>
            <p class="text-xs leading-5 text-slate-400">{notice.message}</p>
          </div>
          <button
            type="button"
            on:click={closeNotice}
            aria-label="Close notification"
            class="h-8 w-8 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
          >
            x
          </button>
        </div>
      </section>
    </div>
  {/if}
</div>
