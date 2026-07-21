<script>
  import { onMount } from 'svelte';
  import LockedState from './LockedState.svelte';
  import { GetFrameworkInfo, GetGlobalConfig, RunDoctor, SaveGlobalConfig, UpdateFrameworkSource, InstallFramework } from '../../wailsjs/go/main/App';

  export let selectedProject = null;

  let doctorOutput = null;
  let isRunningDoctor = false;
  let updateLog = '';
  let isUpdating = false;
  let installLog = '';
  let isInstalling = false;
  let frameworkInfo = { name: 'AIWF Framework', version: 'unknown', repository: '', available: false, cli_installed: false, project_installed: false };
  let globalConfig = { telegram_bot_token_configured: false, telegram_proxy: '' };
  let telegramTokenInput = '';
  let telegramProxyInput = '';
  let isSavingConfig = false;
  let configLog = '';

  onMount(async () => {
    try {
      frameworkInfo = await GetFrameworkInfo();
      globalConfig = await GetGlobalConfig();
      telegramProxyInput = globalConfig.telegram_proxy || '';
    } catch (err) {
      updateLog = 'Unable to read framework metadata: ' + err;
    }
  });

  async function handleInstallFramework() {
    if (isInstalling) return;
    isInstalling = true;
    installLog = 'Starting AIWF Framework installation & bootstrap...\n';
    try {
      const result = await InstallFramework();
      if (result.success) {
        installLog += '\nAIWF Framework installation completed successfully!\n\nLogs:\n' + result.stdout;
        // Refresh framework info
        frameworkInfo = await GetFrameworkInfo();
      } else {
        installLog += `\nAIWF Framework installation failed (Exit Code ${result.exit_code || result.exitCode}):\n\nLogs:\n` + result.stdout;
      }
    } catch (err) {
      installLog += '\nAIWF Framework installation failed with error: ' + err;
    } finally {
      isInstalling = false;
    }
  }

  async function handleRunDoctor() {
    if (isRunningDoctor) return;
    isRunningDoctor = true;
    doctorOutput = null;
    try {
      const report = await RunDoctor();
      doctorOutput = report;
    } catch (err) {
      doctorOutput = {
        status: 'ERROR',
        environment: { error: String(err) },
        toolchain: {}
      };
    } finally {
      isRunningDoctor = false;
    }
  }

  async function handleUpdateSource() {
    if (isUpdating) return;
    isUpdating = true;
    updateLog = `Updating AIWF framework source from ${frameworkInfo.repository || 'configured Git remote'}...`;
    try {
      const result = await UpdateFrameworkSource();
      if (result.success) {
        frameworkInfo = await GetFrameworkInfo();
        updateLog = 'AIWF framework source update completed:\n' + result.stdout;
      } else {
        updateLog = 'AIWF framework source update failed:\n' + result.stdout + '\n' + result.stderr;
      }
    } catch (err) {
      updateLog = 'AIWF framework source update failed: ' + err;
    }
    isUpdating = false;
  }

  async function handleSaveGlobalConfig() {
    if (isSavingConfig) return;
    isSavingConfig = true;
    configLog = 'Saving global AIWF configuration...';
    try {
      globalConfig = await SaveGlobalConfig(telegramTokenInput, telegramProxyInput);
      telegramTokenInput = '';
      telegramProxyInput = globalConfig.telegram_proxy || '';
      configLog = 'Global AIWF configuration saved.';
    } catch (err) {
      configLog = 'Global AIWF configuration failed: ' + err;
    } finally {
      isSavingConfig = false;
    }
  }
</script>

<div class="space-y-6">
  <div>
    <h2 class="text-xl font-bold text-slate-100">System Diagnostics & Framework Source</h2>
    <p class="text-xs text-slate-400 mt-1">Manage AIWF framework source globally and run workspace diagnostics for the selected project.</p>
  </div>

  <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-5">
    <div class="border-b border-slate-700/60 pb-3 flex items-center justify-between">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-emerald-400 font-mono">AIWF Framework Management</h3>
      <span class="text-[10px] text-slate-400 font-mono">Version: v{frameworkInfo.version}</span>
    </div>

    <!-- Status Indicators -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- 1. Framework Source -->
      <div class="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex flex-col justify-between space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-[10px] uppercase font-mono text-slate-400">Framework Source</span>
          <span class="inline-flex h-2.5 w-2.5 rounded-full {frameworkInfo.available ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]'}"></span>
        </div>
        <div>
          <div class="text-sm font-bold {frameworkInfo.available ? 'text-emerald-400' : 'text-amber-400'}">
            {frameworkInfo.available ? 'Source Ready' : 'Source Missing'}
          </div>
          <p class="text-[10px] text-slate-500 mt-1 truncate" title={frameworkInfo.source_root}>
            {frameworkInfo.available ? frameworkInfo.source_root : 'Requires clone from GitHub'}
          </p>
        </div>
      </div>

      <!-- 2. Global CLI -->
      <div class="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex flex-col justify-between space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-[10px] uppercase font-mono text-slate-400">Global CLI Path</span>
          <span class="inline-flex h-2.5 w-2.5 rounded-full {frameworkInfo.cli_installed ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]'}"></span>
        </div>
        <div>
          <div class="text-sm font-bold {frameworkInfo.cli_installed ? 'text-emerald-400' : 'text-amber-400'}">
            {frameworkInfo.cli_installed ? 'CLI Installed' : 'Not Installed'}
          </div>
          <p class="text-[10px] text-slate-500 mt-1">
            {frameworkInfo.cli_installed ? 'global "aiwf" command ready' : 'Requires bootstrap run'}
          </p>
        </div>
      </div>

      <!-- 3. Project Workspace -->
      <div class="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex flex-col justify-between space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-[10px] uppercase font-mono text-slate-400">Active Project</span>
          <span class="inline-flex h-2.5 w-2.5 rounded-full {!selectedProject ? 'bg-slate-600' : (frameworkInfo.project_installed ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]')}"></span>
        </div>
        <div>
          <div class="text-sm font-bold {!selectedProject ? 'text-slate-400' : (frameworkInfo.project_installed ? 'text-emerald-400' : 'text-amber-400')}">
            {!selectedProject ? 'No Project Selected' : (frameworkInfo.project_installed ? 'Configured (.agents)' : 'Not Configured')}
          </div>
          <p class="text-[10px] text-slate-500 mt-1 truncate" title={selectedProject ? selectedProject.path : ''}>
            {selectedProject ? selectedProject.name : 'Select project to install'}
          </p>
        </div>
      </div>
    </div>

    <!-- Actions panel -->
    <div class="flex flex-wrap gap-3 pt-2">
      <button
        on:click={handleInstallFramework}
        disabled={isInstalling}
        class="bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 text-slate-950 font-bold px-5 py-3 rounded-xl text-xs transition-all shadow-md shrink-0 disabled:border-transparent border border-sky-400/20"
      >
        {isInstalling ? 'Installing Framework...' : 'Install & Bootstrap AIWF'}
      </button>

      <button
        on:click={handleUpdateSource}
        disabled={isUpdating || !frameworkInfo.available}
        class="bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-600 text-slate-200 border border-slate-600 px-5 py-3 rounded-xl font-semibold text-xs transition-all shrink-0"
      >
        {isUpdating ? 'Updating Source...' : 'Update Framework Source'}
      </button>
    </div>
  </div>

  {#if installLog}
    <div class="space-y-1.5">
      <div class="text-[10px] uppercase font-mono text-slate-400 font-bold">Installation Logs</div>
      <pre class="p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-96 app-scrollbar border-l-4 border-l-sky-500 shadow-inner">
        {installLog}
      </pre>
    </div>
  {/if}

  {#if updateLog}
    <div class="space-y-1.5">
      <div class="text-[10px] uppercase font-mono text-slate-400 font-bold">Update Logs</div>
      <pre class="p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-96 app-scrollbar border-l-4 border-l-emerald-500 shadow-inner">
        {updateLog}
      </pre>
    </div>
  {/if}

  <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-4">
    <div class="space-y-1">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-sky-400 font-mono">Global Telegram Configuration</h3>
      <p class="text-xs text-slate-400">
        Configure shared AIWF Telegram credentials used by all registered projects. The current bot token is never displayed after saving.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-[1fr_1fr_auto] gap-3 items-end">
      <div class="space-y-1.5">
        <label for="telegramBotToken" class="text-[10px] font-mono text-slate-400 uppercase">Bot Token</label>
        <input
          id="telegramBotToken"
          type="password"
          bind:value={telegramTokenInput}
          placeholder={globalConfig.telegram_bot_token_configured ? 'Configured. Enter a new token to replace it.' : 'Enter Telegram bot token...'}
          class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
        />
      </div>

      <div class="space-y-1.5">
        <label for="telegramProxy" class="text-[10px] font-mono text-slate-400 uppercase">Proxy</label>
        <input
          id="telegramProxy"
          type="text"
          bind:value={telegramProxyInput}
          placeholder="Optional. Example: http://127.0.0.1:8080"
          class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
        />
      </div>

      <button
        type="button"
        on:click={handleSaveGlobalConfig}
        disabled={isSavingConfig || (!telegramTokenInput.trim() && !globalConfig.telegram_bot_token_configured)}
        class="bg-sky-500 hover:bg-sky-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 px-5 py-2.5 rounded-xl font-bold text-xs shadow transition-all border border-sky-400 shrink-0"
      >
        {isSavingConfig ? 'Saving...' : 'Save Config'}
      </button>
    </div>

    <div class="flex flex-wrap gap-2 text-[10px] font-mono">
      <span class="rounded-full px-2.5 py-1 {globalConfig.telegram_bot_token_configured ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'}">
        Token: {globalConfig.telegram_bot_token_configured ? 'Configured' : 'Missing'}
      </span>
      <span class="rounded-full px-2.5 py-1 bg-slate-700/40 text-slate-400">
        Proxy: {globalConfig.telegram_proxy ? 'Configured' : 'Direct'}
      </span>
    </div>

    {#if configLog}
      <div class="rounded-xl border border-slate-700/80 bg-slate-900 p-3 font-mono text-xs text-sky-300">
        {configLog}
      </div>
    {/if}
  </div>

  {#if !selectedProject}
    <LockedState featureName="Workspace Diagnostics" on:navigateToProjects />
  {:else}
    <div class="space-y-4">
      <div>
        <h3 class="text-xs font-semibold uppercase tracking-wider text-sky-400 font-mono">Selected Project Diagnostics</h3>
        <p class="text-xs text-slate-400 mt-1">Run workspace doctor against the selected project context.</p>
      </div>
      <button
        on:click={handleRunDoctor}
        disabled={isRunningDoctor}
        class="bg-sky-500 hover:bg-sky-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 px-4 py-2.5 rounded-xl font-bold text-xs shadow transition-all border border-sky-400"
      >
        {isRunningDoctor ? '🩺 Running Doctor...' : '🩺 Run System Doctor'}
      </button>
    </div>

    {#if doctorOutput}
      <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-4">
        <div class="flex items-center justify-between border-b border-slate-700 pb-3">
          <h3 class="text-sm font-bold text-slate-100 font-mono">Workspace Doctor Diagnostics Report</h3>
          <span class="px-2.5 py-1 rounded-full font-semibold text-[10px] uppercase font-mono
            {doctorOutput.status === 'READY' || doctorOutput.status === 'SUCCESS' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}">
            {doctorOutput.status}
          </span>
        </div>

        {#if doctorOutput.environment && doctorOutput.environment.error}
          <div class="p-3 bg-rose-950/20 border border-rose-500/20 rounded-lg text-xs text-rose-400 font-mono">
            {doctorOutput.environment.error}
          </div>
        {:else}
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            {#if doctorOutput.toolchain && doctorOutput.toolchain.python}
              <div class="p-3 bg-slate-900 rounded-lg">
                <div class="text-slate-400 text-[10px] uppercase">Python</div>
                <div class="font-bold text-slate-200 mt-1">{doctorOutput.toolchain.python.version || 'Installed'}</div>
              </div>
            {/if}
            {#if doctorOutput.toolchain && doctorOutput.toolchain.golang}
              <div class="p-3 bg-slate-900 rounded-lg">
                <div class="text-slate-400 text-[10px] uppercase">Golang</div>
                <div class="font-bold text-slate-200 mt-1">{doctorOutput.toolchain.golang.version || 'Installed'}</div>
              </div>
            {/if}
            {#if doctorOutput.toolchain && doctorOutput.toolchain.node}
              <div class="p-3 bg-slate-900 rounded-lg">
                <div class="text-slate-400 text-[10px] uppercase">Node.js</div>
                <div class="font-bold text-slate-200 mt-1">{doctorOutput.toolchain.node.version || 'Installed'}</div>
              </div>
            {/if}
            {#if doctorOutput.toolchain && doctorOutput.toolchain.git}
              <div class="p-3 bg-slate-900 rounded-lg">
                <div class="text-slate-400 text-[10px] uppercase">Git</div>
                <div class="font-bold text-slate-200 mt-1">{doctorOutput.toolchain.git.version || 'Installed'}</div>
              </div>
            {/if}
          </div>

          {#if doctorOutput.environment}
            <div class="p-3 bg-slate-900 rounded-lg text-xs font-mono space-y-1">
              <div class="text-slate-400 text-[10px] uppercase font-bold">Environment Metadata</div>
              <div class="text-slate-300">OS: {doctorOutput.environment.os || 'N/A'}</div>
              <div class="text-slate-300">Virtual Env: {doctorOutput.environment.virtual_env || 'none'}</div>
            </div>
          {/if}
        {/if}
      </div>
    {/if}
  {/if}
</div>
