<script>
  export let prompt = {
    pending: false,
    question: 'Approve Technical Design Blueprint for implementation?',
    options: ['Continue', 'Cancel']
  };
  export let onSelect = (choice) => {};

  function handleSelect(option) {
    if (onSelect) onSelect(option);
  }
</script>

{#if prompt && prompt.pending}
  <div class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-slate-900 border border-sky-500/30 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold text-lg">
          ?
        </div>
        <div>
          <h3 class="text-lg font-bold text-slate-100">Approval Required</h3>
          <p class="text-xs text-slate-400">AI Engineering Workflow Gate</p>
        </div>
      </div>

      <div class="p-4 bg-slate-800/60 rounded-xl border border-slate-700/50 text-sm text-slate-200">
        {prompt.question}
      </div>

      <div class="flex justify-end gap-3">
        {#each prompt.options as option}
          <button
            on:click={() => handleSelect(option)}
            class="px-5 py-2.5 rounded-xl font-semibold text-sm transition-all shadow-md
                   {option === 'Continue' ? 'bg-sky-500 hover:bg-sky-400 text-slate-950' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'}"
          >
            {option}
          </button>
        {/each}
      </div>
    </div>
  </div>
{/if}
