<script>
  export let runtimeState = {
    current_skill: 'initialize-workflow',
    current_command: 'init',
    current_step: 'Initialization Complete',
    status: 'completed',
    checkpoint: 1
  };
</script>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <!-- Active Skill Card -->
  <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-md">
    <div class="text-xs font-semibold uppercase tracking-wider text-sky-400 mb-1">Active Skill</div>
    <div class="text-xl font-bold text-slate-100">{runtimeState.current_skill || 'Idle'}</div>
    <div class="text-xs text-slate-400 mt-2 font-mono">Command: {runtimeState.current_command || 'N/A'}</div>
  </div>

  <!-- Current Step Card -->
  <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-md">
    <div class="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1">Current Step</div>
    <div class="text-sm font-medium text-slate-200 line-clamp-2">{runtimeState.current_step || 'Awaiting task...'}</div>
    <div class="text-xs text-slate-400 mt-2">Checkpoint: {runtimeState.checkpoint || 1} / 10</div>
  </div>

  <!-- Status Badge Card -->
  <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-md flex flex-col justify-between">
    <div class="text-xs font-semibold uppercase tracking-wider text-purple-400 mb-1">Execution Status</div>
    <div class="flex items-center gap-2">
      <span class="inline-block w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
      <span class="text-lg font-bold uppercase tracking-wide text-slate-100">{runtimeState.status || 'READY'}</span>
    </div>
    <div class="text-xs text-slate-500 mt-2">Engine: In-Process Lightweight Daemon</div>
  </div>
</div>
