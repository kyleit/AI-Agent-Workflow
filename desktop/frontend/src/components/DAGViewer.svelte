<script>
  // Dynamic Svelte Component rendering workflow DAG nodes & edges
  export let tasks = []; // Array of { id, description, status, dependencies: [] }

  // Simple layout calculation for task nodes
  // In a real application, a layout algorithm like Dagre or custom node positioning would be used.
  // Here we calculate visual coordinates dynamically in columns based on task dependencies hierarchy.
  $: columns = calculateLayout(tasks);

  function calculateLayout(taskList) {
    if (!taskList || taskList.length === 0) return [];
    
    // Group tasks by dependency levels
    const levels = [];
    const visited = new Set();
    let remaining = [...taskList];

    while (remaining.length > 0) {
      const currentLevel = remaining.filter(task => {
        const deps = task.dependencies || [];
        return deps.every(dep => visited.has(dep));
      });

      if (currentLevel.length === 0) {
        // Fallback for circular references or unresolved deps
        levels.push(remaining);
        break;
      }

      levels.push(currentLevel);
      currentLevel.forEach(t => visited.add(t.id));
      remaining = remaining.filter(t => !visited.has(t.id));
    }
    
    return levels;
  }

  function getStatusColor(status) {
    switch (status) {
      case "success": return "#10B981"; // Emerald green
      case "running": return "#3B82F6"; // Blue
      case "failed": return "#EF4444";  // Red
      case "pending":
      default: return "#6B7280";       // Cool gray
    }
  }
</script>

<div class="w-full h-96 bg-slate-900 rounded-lg p-4 border border-slate-700 overflow-auto flex flex-col items-center justify-center">
  {#if tasks.length === 0}
    <p class="text-slate-400 text-sm">Không có tác vụ nào đang hoạt động trên Đồ thị DAG.</p>
  {:else}
    <svg class="w-full h-full min-w-[600px]" viewBox="0 0 800 350">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 2 L 10 5 L 0 8 z" fill="#475569" />
        </marker>
      </defs>

      <!-- Draw Task Nodes -->
      {#each columns as level, colIndex}
        {#each level as task, rowIndex}
          {@const x = 50 + colIndex * 220}
          {@const y = 50 + rowIndex * 80}
          <g class="transition-transform duration-300">
            <!-- Node Box -->
            <rect 
              x={x} y={y} 
              width="160" height="50" 
              rx="6" 
              fill="#1e293b" 
              stroke={getStatusColor(task.status)} 
              stroke-width="2" 
            />
            <!-- Node Content -->
            <text x={x + 10} y={y + 22} fill="#f8fafc" font-size="12" font-weight="bold">{task.id}</text>
            <text x={x + 10} y={y + 40} fill="#94a3b8" font-size="10">{task.description.substring(0, 22)}...</text>

            <!-- Draw status dot -->
            <circle cx={x + 145} cy={y + 15} r="5" fill={getStatusColor(task.status)} />
          </g>
        {/each}
      {/each}
    </svg>
  {/if}
</div>

<style>
  svg {
    user-select: none;
  }
</style>
