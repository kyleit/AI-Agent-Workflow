<script>
  let promptText = '';
  export let onRun = (prompt) => {};
  export let disabled = false;

  function handleSubmit() {
    if (!promptText.trim() || disabled) return;
    if (onRun) onRun(promptText);
    promptText = '';
  }
</script>

<div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-md space-y-4">
  <div class="flex items-center justify-between">
    <h3 class="text-sm font-semibold uppercase tracking-wider text-slate-300 font-mono">Quick Workflow Launcher</h3>
    <span class="text-xs px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">coordinator.py</span>
  </div>

  <form on:submit|preventDefault={handleSubmit} class="space-y-3">
    <input
      type="text"
      bind:value={promptText}
      disabled={disabled}
      placeholder="Describe the feature or bug to fix (e.g. Add article filter)..."
      class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors disabled:opacity-50"
    />
    <div class="flex justify-end">
      <button
        type="submit"
        disabled={disabled || !promptText.trim()}
        class="bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 px-5 py-2.5 rounded-xl font-bold text-sm transition-all shadow-md flex items-center gap-2 border border-emerald-400"
      >
        <span>🚀 Run Workflow</span>
      </button>
    </div>
  </form>
</div>
