<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let projects = [];
  export let selectedProject = null;

  let scanRoot = '';
  let scanStatus = 'Choose a parent folder and scan for project workspaces.';
  let scanCandidates = [];
  let isScanning = false;
  let pendingDeleteProject = null;

  function handleScanProjects() {
    isScanning = true;
    scanStatus = 'Waiting for folder selection...';
    dispatch('scanProjects', {
      onResult: (candidates, root) => {
        scanRoot = root;
        scanCandidates = candidates || [];
        isScanning = false;
        scanStatus = root
          ? `Found ${scanCandidates.length} candidate workspace(s).`
          : 'Scan cancelled.';
      },
      onError: (message) => {
        scanCandidates = [];
        isScanning = false;
        scanStatus = message || 'Project scan failed.';
      }
    });
  }

  function handleRegisterCandidate(candidate) {
    dispatch('registerProject', { name: candidate.name, path: candidate.path });
  }

  function handleSelect(project) {
    dispatch('selectProject', { path: project.path });
  }

  function handleDelete(project) {
    pendingDeleteProject = project;
  }

  function cancelDelete() {
    pendingDeleteProject = null;
  }

  function confirmDelete() {
    if (!pendingDeleteProject) return;
    const project = pendingDeleteProject;
    pendingDeleteProject = null;
    dispatch('deleteProject', { id: project.id });
  }

  function telegramLabel(project) {
    if (!project.telegram_chat_id) return 'Not linked';
    return project.telegram_title || project.telegram_chat_id;
  }

  function compactPath(path) {
    if (!path) return '';
    const normalized = path.replace(/\\/g, '/');
    const prefix = normalized.startsWith('/') ? '/' : '';
    const parts = normalized.split('/').filter(Boolean);
    if (parts.length <= 4) return path;
    return `${prefix}${parts[0]}/${parts[1]}/.../${parts[parts.length - 2]}/${parts[parts.length - 1]}`;
  }

  function registeredProjectFor(path) {
    return projects.find((project) => project.path === path);
  }
</script>

<div class="space-y-6">
  <div>
    <h2 class="text-xl font-bold text-slate-100">Projects Registry</h2>
    <p class="text-xs text-slate-400 mt-1">Manage and register project workspaces in the AIWF ecosystem (aiwf registry)</p>
  </div>

  <div class="rounded-xl border border-slate-700/60 bg-slate-800/80 p-5 shadow-lg space-y-4">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="min-w-0 space-y-2">
        <h3 class="font-mono text-xs font-semibold uppercase tracking-wider text-sky-400">Scan Project Workspaces</h3>
        <p class="max-w-2xl text-xs leading-5 text-slate-400">
          Pick a parent folder, scan for likely project workspaces, then register one from the list. Paths are selected from scan results only.
        </p>
        {#if scanRoot}
          <p class="font-mono text-[11px] text-slate-500 truncate" title={scanRoot}>
            Root: {compactPath(scanRoot)}
          </p>
        {/if}
      </div>
      <button
        type="button"
        on:click={handleScanProjects}
        disabled={isScanning}
        class="shrink-0 rounded-xl border border-sky-400 bg-sky-500 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-md transition-all hover:bg-sky-400 disabled:border-slate-700 disabled:bg-slate-700 disabled:text-slate-500"
      >
        {isScanning ? 'Scanning...' : 'Scan Folder'}
      </button>
    </div>

    <div class="rounded-xl border border-slate-700/70 bg-slate-900/70 p-3 text-xs text-slate-400">
      {scanStatus}
    </div>

    {#if scanCandidates.length > 0}
      <div class="max-h-72 overflow-y-auto rounded-xl border border-slate-700/70 app-scrollbar">
        <table class="w-full table-fixed border-collapse text-left text-xs">
          <thead class="sticky top-0 bg-slate-900 text-[10px] uppercase text-slate-500">
            <tr>
              <th class="w-[26%] p-3">Workspace</th>
              <th class="w-[42%] p-3">Path</th>
              <th class="w-[16%] p-3">Type</th>
              <th class="w-[16%] p-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            {#each scanCandidates as candidate}
              {@const registered = registeredProjectFor(candidate.path)}
              <tr class="hover:bg-slate-800/60">
                <td class="p-3 font-semibold text-slate-100 truncate" title={candidate.name}>{candidate.name}</td>
                <td class="p-3 font-mono text-[11px] text-slate-400">
                  <span class="block truncate" title={candidate.path}>{compactPath(candidate.path)}</span>
                </td>
                <td class="p-3 text-[11px] text-slate-400">{candidate.kind}</td>
                <td class="p-3">
                  {#if registered}
                    <button
                      type="button"
                      on:click={() => handleSelect(registered)}
                      class="text-xs font-semibold text-emerald-400 hover:text-emerald-300"
                    >
                      Select
                    </button>
                  {:else}
                    <button
                      type="button"
                      on:click={() => handleRegisterCandidate(candidate)}
                      class="text-xs font-semibold text-sky-400 hover:text-sky-300"
                    >
                      Register
                    </button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>

  <div class="rounded-xl border border-slate-700/60 bg-slate-800/80 shadow-lg overflow-hidden">
    <div class="overflow-x-auto app-scrollbar">
      <table class="w-full min-w-[920px] table-fixed border-collapse text-left text-xs">
        <thead>
          <tr class="border-b border-slate-700 bg-slate-900/80 font-mono text-[10px] uppercase text-slate-400">
            <th class="w-[24%] p-4">Project Name</th>
            <th class="w-[30%] p-4">Workspace Path</th>
            <th class="w-[18%] p-4">Telegram</th>
            <th class="w-[12%] p-4">Status</th>
            <th class="w-[16%] p-4">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-700/50">
          {#if projects.length === 0}
            <tr>
              <td colspan="5" class="p-8 text-center font-medium text-slate-500">
                No projects registered. Scan a parent folder above to register your first project.
              </td>
            </tr>
          {:else}
            {#each projects as project}
              <tr class="hover:bg-slate-700/30 transition-colors">
                <td class="p-4 font-semibold text-slate-100 truncate" title={project.name}>{project.name}</td>
                <td class="p-4 font-mono text-[11px] text-slate-400">
                  <span class="block max-w-full truncate" title={project.path}>{compactPath(project.path)}</span>
                </td>
                <td class="p-4">
                  {#if project.telegram_chat_id}
                    <div class="space-y-1">
                      <div class="truncate text-xs font-semibold text-slate-200" title={telegramLabel(project)}>{telegramLabel(project)}</div>
                      <div class="truncate font-mono text-[10px] text-slate-500" title={project.telegram_chat_id}>{project.telegram_chat_id}</div>
                    </div>
                  {:else}
                    <span class="rounded-full bg-slate-700/40 px-2.5 py-1 text-[10px] font-medium text-slate-400">Not linked</span>
                  {/if}
                </td>
                <td class="p-4">
                  {#if selectedProject && selectedProject.path === project.path}
                    <span class="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-400">Active</span>
                  {:else}
                    <span class="rounded-full bg-slate-700/40 px-2.5 py-1 text-[10px] font-medium text-slate-400">Registered</span>
                  {/if}
                </td>
                <td class="p-4">
                  <div class="flex items-center gap-3">
                    {#if !selectedProject || selectedProject.path !== project.path}
                      <button
                        type="button"
                        on:click={() => handleSelect(project)}
                        class="text-xs font-semibold text-sky-400 transition-colors hover:text-sky-300"
                      >
                        Select
                      </button>
                      <span class="text-slate-600">|</span>
                    {/if}
                    <button
                      type="button"
                      on:click={() => handleDelete(project)}
                      class="text-xs font-semibold text-rose-400 transition-colors hover:text-rose-300"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>

  {#if pendingDeleteProject}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-6">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-project-title"
        class="w-full max-w-md rounded-xl border border-rose-500/30 bg-slate-900 p-5 shadow-2xl"
      >
        <div class="space-y-4">
          <div class="space-y-2">
            <h2 id="delete-project-title" class="text-sm font-bold text-slate-100">Delete Project</h2>
            <p class="text-xs leading-5 text-slate-400">
              Remove <span class="font-semibold text-slate-200">{pendingDeleteProject.name}</span> from the registry?
              This only removes the app registration and does not delete files from disk.
            </p>
            <p class="truncate font-mono text-[11px] text-slate-500" title={pendingDeleteProject.path}>
              {compactPath(pendingDeleteProject.path)}
            </p>
          </div>

          <div class="flex justify-end gap-2">
            <button
              type="button"
              on:click={cancelDelete}
              class="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              type="button"
              on:click={confirmDelete}
              class="rounded-lg border border-rose-400 bg-rose-500 px-4 py-2 text-xs font-bold text-white hover:bg-rose-400"
            >
              Delete
            </button>
          </div>
        </div>
      </section>
    </div>
  {/if}
</div>
