<script>
  // LogStreamer.svelte
  export let logs = []; // Array of log strings: ["[INFO] ...", "[DEBUG] ..."]
  
  let filterText = "";
  
  // Reactively filter logs
  $: filteredLogs = logs.filter(logLine => 
    logLine.toLowerCase().includes(filterText.toLowerCase())
  );
  
  let logContainer;
  
  // Auto-scroll to bottom of logs container when logs update
  $: if (filteredLogs && logContainer) {
    setTimeout(() => {
      logContainer.scrollTop = logContainer.scrollHeight;
    }, 50);
  }

  function clearLogs() {
    logs = [];
  }
</script>

<div class="w-full bg-slate-900 rounded-lg border border-slate-700 flex flex-col h-96">
  <!-- Log Header & Filters -->
  <div class="p-3 border-b border-slate-700 flex items-center justify-between bg-slate-800 rounded-t-lg gap-4">
    <div class="flex items-center gap-2">
      <span class="text-sm font-bold text-slate-200">Log Explorer</span>
      <span class="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{filteredLogs.length} dòng</span>
    </div>
    
    <div class="flex items-center gap-2 flex-1 max-w-xs">
      <input 
        type="text" 
        bind:value={filterText}
        placeholder="Lọc log..." 
        class="w-full bg-slate-950 text-xs text-slate-200 border border-slate-700 rounded px-2 py-1 focus:outline-none focus:border-slate-500"
      />
    </div>

    <button 
      on:click={clearLogs}
      class="text-xs text-slate-400 hover:text-slate-200 bg-slate-750 px-3 py-1 rounded border border-slate-700 transition"
    >
      Xóa
    </button>
  </div>

  <!-- Log Content Container -->
  <div 
    bind:this={logContainer}
    class="flex-1 p-3 overflow-y-auto font-mono text-[10px] text-slate-300 bg-slate-950/80 leading-relaxed scroll-smooth"
  >
    {#if filteredLogs.length === 0}
      <p class="text-slate-500 italic text-center mt-4">Không có dòng log nào khớp với bộ lọc.</p>
    {:else}
      {#each filteredLogs as log}
        <div class="hover:bg-slate-900 py-0.5 border-b border-slate-900/35 break-all whitespace-pre-wrap">
          {log}
        </div>
      {/each}
    {/if}
  </div>
</div>
