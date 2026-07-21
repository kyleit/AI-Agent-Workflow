<script>
  import { WindowMinimise, WindowHide } from '../../wailsjs/runtime/runtime';
  import appIcon from '../assets/icon.png';
</script>

<div class="titlebar-drag fixed top-0 left-0 right-0 h-8 z-50 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-3 select-none">
  <!-- Title / Brand Info -->
  <div class="flex items-center gap-2 pointer-events-none">
    <img src={appIcon} alt="AIWF" class="w-4 h-4 rounded object-cover" />
    <span class="text-xs font-semibold text-slate-300">AIWF Framework</span>
  </div>

  <!-- Window Controls -->
  <div class="titlebar-no-drag flex items-center gap-1">
    <!-- Minimize Button -->
    <button
      on:click={WindowMinimise}
      type="button"
      class="h-6 w-8 rounded text-slate-400 hover:bg-slate-800 hover:text-slate-100 flex items-center justify-center transition-colors text-xs"
      aria-label="Minimize"
    >
      &mdash;
    </button>

    <!-- Close Button -->
    <button
      on:click={WindowHide}
      type="button"
      class="h-6 w-8 rounded text-slate-400 hover:bg-red-600 hover:text-white flex items-center justify-center transition-colors text-xs font-semibold"
      aria-label="Close"
    >
      &times;
    </button>
  </div>
</div>

<style>
  .titlebar-drag {
    --wails-draggable: drag;
    -webkit-app-region: drag;
  }
  .titlebar-no-drag {
    --wails-draggable: no-drag;
    -webkit-app-region: no-drag;
    pointer-events: auto;
  }
</style>
