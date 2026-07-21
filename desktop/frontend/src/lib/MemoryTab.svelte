<script>
  import { createEventDispatcher } from 'svelte';
  import LockedState from './LockedState.svelte';
  import { SearchMemory, RunGenericCommand } from '../../wailsjs/go/main/App';

  const dispatch = createEventDispatcher();

  export let selectedProject = null;

  let queryText = '';
  let searchResults = [];
  let statusLog = '';
  let isSearching = false;
  let isBootstrapping = false;
  let isUpdating = false;

  async function handleBootstrap() {
    if (isBootstrapping) return;
    isBootstrapping = true;
    statusLog = 'Running project memory bootstrap (aiwf memory bootstrap)...';
    try {
      const result = await RunGenericCommand('memory', 'bootstrap', []);
      if (result.success) {
        statusLog = 'Project memory bootstrapped successfully.\n' + result.stdout;
      } else {
        statusLog = 'Error: ' + result.stdout + '\n' + result.stderr;
      }
    } catch (err) {
      statusLog = 'Failed to execute command: ' + err;
    } finally {
      isBootstrapping = false;
    }
  }

  async function handleUpdate() {
    if (isUpdating) return;
    isUpdating = true;
    statusLog = 'Running incremental memory sync (aiwf memory update)...';
    try {
      const result = await RunGenericCommand('memory', 'update', []);
      if (result.success) {
        statusLog = 'Project memory updated incrementally.\n' + result.stdout;
      } else {
        statusLog = 'Error: ' + result.stdout + '\n' + result.stderr;
      }
    } catch (err) {
      statusLog = 'Failed to execute command: ' + err;
    } finally {
      isUpdating = false;
    }
  }

  async function handleSearch() {
    if (!queryText.trim() || isSearching) return;
    isSearching = true;
    try {
      const results = await SearchMemory(queryText);
      searchResults = results || [];
    } catch (err) {
      searchResults = [{ file: 'Error', score: '0.00', match: 'Search failed: ' + err }];
    } finally {
      isSearching = false;
    }
  }
</script>

{#if !selectedProject}
  <LockedState featureName="Project Memory" on:navigateToProjects />
{:else}
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-bold text-slate-100">Project Memory & RAG Search</h2>
      <p class="text-xs text-slate-400 mt-1">Manage project knowledge base and run semantic queries (aiwf memory)</p>
    </div>

    <!-- Actions Bar -->
    <div class="flex gap-3">
      <button
        on:click={handleBootstrap}
        disabled={isBootstrapping || isUpdating}
        class="bg-sky-500 hover:bg-sky-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 px-4 py-2.5 rounded-xl font-bold text-xs shadow transition-all"
      >
        {isBootstrapping ? '🧠 Bootstrapping...' : '🧠 Bootstrap Project Memory'}
      </button>
      <button
        on:click={handleUpdate}
        disabled={isBootstrapping || isUpdating}
        class="bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 px-4 py-2.5 rounded-xl font-bold text-xs shadow transition-all"
      >
        {isUpdating ? '🔄 Syncing...' : '🔄 Sync Incremental Memory'}
      </button>
    </div>

    {#if statusLog}
      <pre class="p-4 bg-slate-900 border border-slate-700/80 rounded-xl font-mono text-xs text-sky-300 overflow-x-auto whitespace-pre-wrap max-h-60">
        {statusLog}
      </pre>
    {/if}

    <!-- RAG Search Box -->
    <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-3">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-purple-400 font-mono">Semantic RAG Search (aiwf memory search)</h3>
      <form on:submit|preventDefault={handleSearch} class="flex gap-3">
        <input
          type="text"
          bind:value={queryText}
          placeholder="Enter keyword or semantic question to query project memory..."
          class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
        />
        <button
          type="submit"
          disabled={isSearching}
          class="bg-purple-600 hover:bg-purple-500 disabled:bg-slate-750 disabled:text-slate-500 text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow transition-all"
        >
          {isSearching ? 'Searching...' : '🔍 Search'}
        </button>
      </form>
    </div>

    <!-- Search Results List -->
    {#if searchResults.length > 0}
      <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-3">
        <h4 class="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">Search Results ({searchResults.length})</h4>
        <div class="space-y-2">
          {#each searchResults as item}
            <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-700/50 flex justify-between items-center text-xs">
              <div>
                <div class="font-bold text-slate-100">{item.file}</div>
                <div class="text-slate-400 text-[11px] mt-0.5">{item.match}</div>
              </div>
              <span class="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono text-[10px]">Score: {item.score}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/if}
