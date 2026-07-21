<script>
  // AgentMonitor.svelte
  export let agents = []; // List of active agents: { id, name, status, role, parent_id, active_tokens, cost_usd }

  // Build tree hierarchy helper
  $: rootAgents = buildAgentTree(agents);

  function buildAgentTree(agentList) {
    const map = {};
    const roots = [];
    
    agentList.forEach(agent => {
      map[agent.id] = { ...agent, children: [] };
    });

    agentList.forEach(agent => {
      if (agent.parent_id && map[agent.parent_id]) {
        map[agent.parent_id].children.push(map[agent.id]);
      } else {
        roots.push(map[agent.id]);
      }
    });

    return roots;
  }
</script>

<div class="w-full bg-slate-900 rounded-lg p-4 border border-slate-700 max-h-96 overflow-y-auto">
  <h3 class="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
    <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
    Giám Sát Subagents Đang Chạy
  </h3>

  {#if agents.length === 0}
    <p class="text-slate-400 text-xs italic">Không có tác nhân subagent nào đang hoạt động.</p>
  {:else}
    <div class="flex flex-col gap-2 font-mono text-xs">
      {#each rootAgents as agent}
        <div class="p-3 bg-slate-800 rounded-md border border-slate-700 flex flex-col gap-1">
          <div class="flex items-center justify-between">
            <span class="text-emerald-400 font-bold">{agent.name} <span class="text-slate-500">[{agent.role}]</span></span>
            <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-950/50 text-emerald-300 border border-emerald-800/50">{agent.status.toUpperCase()}</span>
          </div>
          <div class="text-[10px] text-slate-400 flex gap-4 mt-1">
            <span>Tokens: <strong class="text-slate-200">{agent.active_tokens}</strong></span>
            <span>Cost: <strong class="text-amber-400">${agent.cost_usd.toFixed(4)}</strong></span>
          </div>

          <!-- Recursive render children -->
          {#if agent.children && agent.children.length > 0}
            <div class="border-l border-slate-700 pl-4 mt-2 flex flex-col gap-2">
              {#each agent.children as child}
                <div class="p-2 bg-slate-900 rounded border border-slate-800 flex flex-col gap-1">
                  <div class="flex items-center justify-between">
                    <span class="text-blue-400 font-bold">{child.name} <span class="text-slate-500">[{child.role}]</span></span>
                    <span class="px-2 py-0.5 rounded text-[10px] bg-blue-950/50 text-blue-300 border border-blue-800/50">{child.status.toUpperCase()}</span>
                  </div>
                  <div class="text-[10px] text-slate-400 flex gap-4 mt-1">
                    <span>Tokens: <strong class="text-slate-200">{child.active_tokens}</strong></span>
                    <span>Cost: <strong class="text-amber-400">${child.cost_usd.toFixed(4)}</strong></span>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
