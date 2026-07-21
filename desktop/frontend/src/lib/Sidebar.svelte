<script>
  import { onMount } from 'svelte';
  import { GetFrameworkInfo } from '../../wailsjs/go/main/App';

  import appIcon from '../assets/icon.png';

  export let activeTab = 'visualizer';
  export let onSelectTab = (tab) => {};
  let frameworkInfo = { name: 'AIWF Framework', version: 'unknown', repository: '' };

  const tabs = [
    { id: 'visualizer', label: 'Visualizer Dashboard', icon: '📊' },
    { id: 'projects', label: 'Projects Registry', icon: '📁' },
    { id: 'daemons', label: 'Runtime & Daemons', icon: '⚡' },
    { id: 'memory', label: 'Memory & Knowledge', icon: '🧠' },
    { id: 'system', label: 'System & Updates', icon: '⚙️' },
    { id: 'docs', label: 'Documentation', icon: '📘' }
  ];

  onMount(async () => {
    try {
      frameworkInfo = await GetFrameworkInfo();
    } catch (err) {
      console.error('Failed to load framework info:', err);
    }
  });
</script>

<aside class="fixed top-8 bottom-0 left-0 z-30 flex w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-900">
  <div class="min-h-0 flex-1 space-y-6 overflow-y-auto p-4 app-scrollbar">
    <!-- Brand Logo Header -->
    <div class="flex items-center gap-3 px-2 pt-2">
      <img src={appIcon} alt="AIWF Logo" class="w-9 h-9 rounded-xl shadow-md border border-slate-700/50 object-cover" />
      <div>
    <h1 class="text-base font-bold text-slate-100 tracking-tight">AIWF Framework</h1>
        <p class="text-[10px] text-slate-400 font-mono">Framework v{frameworkInfo.version}</p>
      </div>
    </div>

    <!-- Navigation Menu -->
    <nav class="space-y-1">
      {#each tabs as tab}
        <button
          on:click={() => onSelectTab(tab.id)}
          class="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all text-left
                 {activeTab === tab.id
                   ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 font-semibold shadow-sm'
                   : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}"
        >
          <span class="text-sm">{tab.icon}</span>
          <span>{tab.label}</span>
        </button>
      {/each}
    </nav>
  </div>

  <!-- Footer Info -->
  <div class="m-4 shrink-0 rounded-xl border border-slate-800/80 bg-slate-950/60 px-3 py-3 text-[11px] text-slate-400 space-y-1">
    <div class="font-semibold text-slate-300">Multi-project Control Center</div>
    <div class="text-[10px] text-slate-500">{frameworkInfo.name}</div>
  </div>
</aside>
