<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let featureName = 'This feature';

  function handleGoToProjects() {
    dispatch('navigateToProjects');
  }
</script>

<div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center space-y-6 max-w-lg mx-auto my-12 shadow-2xl backdrop-blur-sm">
  <div class="flex justify-center">
    <div class="w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 text-2xl animate-pulse">
      🔒
    </div>
  </div>

  <div class="space-y-2">
    <h3 class="text-lg font-bold text-slate-100">{featureName} Locked</h3>
    <p class="text-xs text-slate-400 leading-relaxed">
      No active project workspace is selected. To access this workspace tool, please register a project folder or select an existing project from the projects registry tab first.
    </p>
  </div>

  <div class="flex justify-center">
    <button
      on:click={handleGoToProjects}
      class="bg-sky-500 hover:bg-sky-400 text-slate-950 px-5 py-2.5 rounded-xl font-bold text-xs shadow-md transition-all border border-sky-400 flex items-center gap-2"
    >
      📂 Go to Projects Registry
    </button>
  </div>
</div>
