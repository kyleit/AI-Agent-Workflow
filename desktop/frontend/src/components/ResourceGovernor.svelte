<script>
  // ResourceGovernor.svelte
  export let cpuUsage = 0; // percentage
  export let ramUsage = 0; // percentage
  export let tokenBudgetUsed = 0; // percentage or numerical value
  export let totalTokensLimit = 2000000;
  export let currentTokens = 0;

  $: tokenPercent = Math.min(100, (currentTokens / totalTokensLimit) * 100);
</script>

<div class="w-full bg-slate-900 rounded-lg p-4 border border-slate-700 grid grid-cols-3 gap-4">
  <!-- CPU Metric -->
  <div class="bg-slate-850 p-3 rounded border border-slate-750 flex flex-col gap-2">
    <div class="flex justify-between items-center text-xs">
      <span class="text-slate-400 font-bold">CPU Usage</span>
      <span class="text-emerald-400 font-mono">{cpuUsage.toFixed(1)}%</span>
    </div>
    <div class="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden">
      <div 
        class="bg-emerald-500 h-full transition-all duration-500" 
        style="width: {cpuUsage}%"
      ></div>
    </div>
  </div>

  <!-- RAM Metric -->
  <div class="bg-slate-850 p-3 rounded border border-slate-750 flex flex-col gap-2">
    <div class="flex justify-between items-center text-xs">
      <span class="text-slate-400 font-bold">RAM Usage</span>
      <span class="text-blue-400 font-mono">{ramUsage.toFixed(1)}%</span>
    </div>
    <div class="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden">
      <div 
        class="bg-blue-500 h-full transition-all duration-500" 
        style="width: {ramUsage}%"
      ></div>
    </div>
  </div>

  <!-- Token Budget Metric -->
  <div class="bg-slate-850 p-3 rounded border border-slate-750 flex flex-col gap-2">
    <div class="flex justify-between items-center text-xs">
      <span class="text-slate-400 font-bold">Tokens Buffer</span>
      <span class="text-amber-400 font-mono">{currentTokens.toLocaleString()} / {totalTokensLimit.toLocaleString()}</span>
    </div>
    <div class="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden">
      <div 
        class="bg-amber-500 h-full transition-all duration-500" 
        style="width: {tokenPercent}%"
      ></div>
    </div>
  </div>
</div>
