<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { CheckDaemonStatus, StartDaemon, StopDaemon, RestartDaemon, RunGenericCommand, ScanTelegramConversations, UnlinkTelegramConversation } from '../../wailsjs/go/main/App';

  const dispatch = createEventDispatcher();

  export let selectedProject = null;

  let runtimeDaemonStatus = 'CHECKING';
  let telegramDaemonStatus = 'CHECKING';
  let linkStatusLog = '';
  let daemonError = '';
  let intervalId = null;

  let conversations = [];
  let selectedChatId = '';
  let isScanning = false;
  let scanError = '';
  let scanMessage = '';
  let tokenMissing = false;

  let showUnlinkConfirm = false;
  let unlinkTargetConv = null;

  async function updateDaemonStatuses() {
    if (!runtimeDaemonStatus) {
      runtimeDaemonStatus = 'CHECKING';
    }
    if (!telegramDaemonStatus) {
      telegramDaemonStatus = 'CHECKING';
    }

    try {
      runtimeDaemonStatus = await CheckDaemonStatus('runtime');
    } catch (err) {
      runtimeDaemonStatus = 'ERROR: ' + err;
    }

    try {
      telegramDaemonStatus = await CheckDaemonStatus('telegram');
    } catch (err) {
      telegramDaemonStatus = 'ERROR: ' + err;
    }
  }

  async function handleDaemonAction(daemonType, action) {
    if (!selectedProject) return;
    daemonError = '';
    try {
      if (daemonType === 'runtime') {
        runtimeDaemonStatus = 'CHECKING';
      } else if (daemonType === 'telegram') {
        telegramDaemonStatus = 'CHECKING';
      }

      if (action === 'start') {
        await StartDaemon(daemonType);
      } else if (action === 'stop') {
        await StopDaemon(daemonType);
      } else if (action === 'restart') {
        await RestartDaemon(daemonType);
      }
      await updateDaemonStatuses();
    } catch (err) {
      daemonError = `Failed to ${action} ${daemonType} daemon: ${err}`;
      await updateDaemonStatuses();
    }
  }

  function isRunning(status) {
    return status?.startsWith('RUNNING') || status?.includes('ACTIVE');
  }

  function isChecking(status) {
    return !status || status === 'CHECKING';
  }

  function badgeLabel(status) {
    if (isChecking(status)) return 'CHECKING';
    if (isRunning(status)) return 'ACTIVE';
    if (status?.startsWith('ERROR')) return 'ERROR';
    return 'STOPPED';
  }

  async function handleScanConversations() {
    if (!selectedProject) return;
    isScanning = true;
    scanError = '';
    scanMessage = '';
    tokenMissing = false;
    try {
      conversations = await ScanTelegramConversations();
      if (conversations.length === 0) {
        scanMessage = 'No conversations found in bot updates or history cache.';
      }
    } catch (err) {
      const errMsg = String(err);
      if (errMsg.includes('TELEGRAM_BOT_TOKEN') || errMsg.includes('not configured')) {
        tokenMissing = true;
        scanError = 'Telegram Bot Token is not configured. Please go to the "System" tab to configure your token first.';
      } else {
        scanError = 'Error scanning conversations: ' + err;
      }
    } finally {
      isScanning = false;
    }
  }

  async function handleLinkChatId() {
    if (!selectedProject || !selectedChatId) return;
    linkStatusLog = `Linking Telegram Conversation (${selectedChatId})...`;
    try {
      // Run the real CLI link command
      const result = await RunGenericCommand('telegram', 'link', [selectedChatId]);
      if (result.success) {
        linkStatusLog = 'Successfully linked Telegram Conversation.';
        dispatch('refreshProjects');
        await handleScanConversations();
      } else {
        linkStatusLog = 'Failed to link Chat ID:\n' + result.stdout + '\n' + result.stderr;
      }
    } catch (err) {
      linkStatusLog = 'Error linking Chat ID: ' + err;
    }
  }

  function triggerUnlink(conv, needsConfirm) {
    unlinkTargetConv = conv;
    if (needsConfirm) {
      showUnlinkConfirm = true;
    } else {
      executeUnlink(conv.chat_id, conv.linked_project_id);
    }
  }

  function cancelUnlink() {
    showUnlinkConfirm = false;
    unlinkTargetConv = null;
  }

  async function confirmUnlink() {
    if (unlinkTargetConv) {
      const chatId = unlinkTargetConv.chat_id;
      const projId = unlinkTargetConv.linked_project_id;
      showUnlinkConfirm = false;
      unlinkTargetConv = null;
      await executeUnlink(chatId, projId);
    }
  }

  async function executeUnlink(chatId, projId) {
    linkStatusLog = `Unlinking Telegram Conversation...`;
    try {
      await UnlinkTelegramConversation(chatId, projId);
      linkStatusLog = 'Successfully unlinked Telegram Conversation.';
      dispatch('refreshProjects');
      await handleScanConversations();
    } catch (err) {
      linkStatusLog = 'Error unlinking: ' + err;
    }
  }

  onMount(() => {
    updateDaemonStatuses();
    // Poll status every 3 seconds
    intervalId = setInterval(updateDaemonStatuses, 3000);
  });

  onDestroy(() => {
    if (intervalId) clearInterval(intervalId);
  });

  // Reactive updates if selectedProject changes
  $: if (selectedProject) {
    updateDaemonStatuses();
  }
</script>

<div class="space-y-6">
  <div>
    <h2 class="text-xl font-bold text-slate-100">Runtime & Telegram Daemons</h2>
    <p class="text-xs text-slate-400 mt-1">Control AIWF automated background services (aiwf runtime, aiwf telegram)</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <!-- Runtime Daemon Card -->
    <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
          <span>⚡ AIWF Runtime Daemon</span>
        </h3>
        {#if isRunning(runtimeDaemonStatus)}
          <span class="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold text-[10px] font-mono">ACTIVE</span>
        {:else if isChecking(runtimeDaemonStatus)}
          <span class="px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/20 font-semibold text-[10px] font-mono">CHECKING</span>
        {:else if runtimeDaemonStatus.startsWith('ERROR')}
          <span class="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-semibold text-[10px] font-mono">ERROR</span>
        {:else}
          <span class="px-2.5 py-1 rounded-full bg-slate-700/40 text-slate-400 font-medium text-[10px] font-mono">STOPPED</span>
        {/if}
      </div>
      <p class="text-xs text-slate-400">The runtime background service monitors sessions, saves workflow state checkpoints, and handles automatic ticks.</p>
      <div class="p-3 bg-slate-900/80 rounded-lg font-mono text-xs text-slate-300">
        Status: {badgeLabel(runtimeDaemonStatus) === 'CHECKING' ? 'Checking daemon status...' : runtimeDaemonStatus}
      </div>
      <div class="flex gap-2">
        {#if !selectedProject}
          <span class="text-[10px] font-mono text-amber-400 italic">Select project to control daemon</span>
        {:else if isChecking(runtimeDaemonStatus)}
          <button disabled class="bg-slate-700/60 text-slate-500 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-wait">Checking...</button>
          <button on:click={updateDaemonStatuses} class="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-200 border border-slate-650 transition-colors">Status Info</button>
        {:else}
          {#if isRunning(runtimeDaemonStatus)}
            <button on:click={() => handleDaemonAction('runtime', 'restart')} class="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-200 border border-slate-650 transition-colors">Restart</button>
            <button on:click={() => handleDaemonAction('runtime', 'stop')} class="bg-rose-500/85 hover:bg-rose-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors">Stop</button>
          {:else}
            <button on:click={() => handleDaemonAction('runtime', 'start')} class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors shadow">Start</button>
          {/if}
          <button on:click={updateDaemonStatuses} class="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-200 border border-slate-650 transition-colors">Status Info</button>
        {/if}
      </div>
    </div>

    <!-- Telegram Daemon Card -->
    <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
          <span>✈️ Shared Telegram Daemon</span>
        </h3>
        {#if isRunning(telegramDaemonStatus)}
          <span class="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold text-[10px] font-mono">ACTIVE</span>
        {:else if isChecking(telegramDaemonStatus)}
          <span class="px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/20 font-semibold text-[10px] font-mono">CHECKING</span>
        {:else if telegramDaemonStatus.startsWith('ERROR')}
          <span class="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-semibold text-[10px] font-mono">ERROR</span>
        {:else}
          <span class="px-2.5 py-1 rounded-full bg-slate-700/40 text-slate-400 font-medium text-[10px] font-mono">STOPPED</span>
        {/if}
      </div>
      <p class="text-xs text-slate-400">The Telegram bot daemon pushes instant status updates and interactive approval notifications to your device.</p>
      <div class="p-3 bg-slate-900/80 rounded-lg font-mono text-xs text-slate-300">
        Status: {badgeLabel(telegramDaemonStatus) === 'CHECKING' ? 'Checking daemon status...' : telegramDaemonStatus}
      </div>
      <div class="flex gap-2">
        {#if !selectedProject}
          <span class="text-[10px] font-mono text-amber-400 italic">Select project to control daemon</span>
        {:else if isChecking(telegramDaemonStatus)}
          <button disabled class="bg-slate-700/60 text-slate-500 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-wait">Checking...</button>
          <button on:click={updateDaemonStatuses} class="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-200 border border-slate-650 transition-colors">Status Info</button>
        {:else}
          {#if isRunning(telegramDaemonStatus)}
            <button on:click={() => handleDaemonAction('telegram', 'restart')} class="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-200 border border-slate-650 transition-colors">Restart</button>
            <button on:click={() => handleDaemonAction('telegram', 'stop')} class="bg-rose-500/85 hover:bg-rose-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors">Stop</button>
          {:else}
            <button on:click={() => handleDaemonAction('telegram', 'start')} class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors shadow">Start</button>
          {/if}
          <button on:click={updateDaemonStatuses} class="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-200 border border-slate-650 transition-colors">Status Info</button>
        {/if}
      </div>
    </div>
  </div>

  {#if daemonError}
    <div class="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-200">
      <div class="flex items-start justify-between gap-4">
        <p>{daemonError}</p>
        <button
          type="button"
          on:click={() => daemonError = ''}
          aria-label="Dismiss daemon error"
          class="h-7 w-7 rounded-lg border border-rose-400/30 bg-rose-500/10 text-rose-100 hover:bg-rose-500/20"
        >
          x
        </button>
      </div>
    </div>
  {/if}

  <!-- Telegram Link Form (Project-bound) -->
  <div class="bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-4 relative overflow-hidden">
    {#if !selectedProject}
      <div class="absolute inset-0 bg-slate-900/80 backdrop-blur-[2px] flex items-center justify-center z-10 p-4">
        <div class="text-center space-y-1">
          <p class="text-xs font-bold text-slate-300">🔒 Telegram configuration locked</p>
          <p class="text-[10px] text-slate-500">Please select an active project workspace to link Telegram Conversation.</p>
        </div>
      </div>
    {/if}

    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-sky-400 font-mono">Link Telegram Conversation (aiwf telegram link)</h3>
      <button
        on:click={handleScanConversations}
        disabled={isScanning || !selectedProject}
        class="bg-sky-500 hover:bg-sky-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 px-3 py-1.5 rounded-lg font-bold text-[10px] uppercase font-mono shadow transition-all border border-sky-400 shrink-0"
      >
        {isScanning ? 'Scanning...' : 'Scan Conversations'}
      </button>
    </div>

    <!-- Error message -->
    {#if scanError}
      <div class="p-3 bg-rose-950/20 border border-rose-500/20 rounded-lg text-xs text-rose-300 space-y-2">
        <p class="font-semibold">⚠️ {scanError}</p>
        {#if tokenMissing}
          <p class="text-[10px] text-slate-400">
            Hướng dẫn: Hãy mở tab <strong>System</strong>, cấu hình bot token (TELEGRAM_BOT_TOKEN) và proxy (nếu có), sau đó quay lại đây và nhấn <strong>Scan Conversations</strong>.
          </p>
        {/if}
      </div>
    {/if}

    {#if scanMessage}
      <div class="p-3 bg-amber-950/20 border border-amber-500/20 rounded-lg text-xs text-amber-300 space-y-2">
        <p class="font-semibold">ℹ️ {scanMessage}</p>
        <p class="text-[10px] text-slate-400">
          Hướng dẫn: Để bot nhận diện được cuộc hội thoại, bạn cần mở ứng dụng Telegram, tìm bot và gửi ít nhất 1 tin nhắn vào nhóm hoặc cuộc trò chuyện cá nhân của bot, sau đó thử nhấn <strong>Scan Conversations</strong> lại.
        </p>
      </div>
    {/if}

    {#if conversations.length > 0}
      <div class="space-y-2">
        <p class="text-[10px] uppercase tracking-wider font-mono text-slate-400">Select Conversation:</p>
        <div class="max-h-60 overflow-y-auto border border-slate-700/80 rounded-xl bg-slate-900/50 p-2 space-y-1.5 app-scrollbar">
          {#each conversations as conv}
            <!-- svelte-ignore a11y-click-events-have-key-events -->
            <!-- svelte-ignore a11y-no-static-element-interactions -->
            <div
              on:click={() => {
                if (!conv.linked_to_other_project && !conv.linked_to_current_project) {
                  selectedChatId = conv.chat_id;
                }
              }}
              class="flex items-center justify-between p-3 rounded-lg border transition-all {conv.linked_to_other_project || conv.linked_to_current_project ? 'border-slate-800 bg-slate-950/20 cursor-not-allowed opacity-75' : selectedChatId === conv.chat_id ? 'border-sky-500 bg-sky-500/10 cursor-pointer' : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-900/40 cursor-pointer'}"
            >
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-slate-200">{conv.title}</span>
                  {#if conv.type}
                    <span class="px-1.5 py-0.5 rounded text-[8px] font-mono uppercase bg-slate-800 text-slate-400 border border-slate-700">{conv.type}</span>
                  {/if}
                </div>
                <div class="text-[10px] text-slate-500 font-mono">Chat ID: {conv.chat_id}</div>
                {#if conv.linked_to_other_project}
                  <div class="text-[10px] text-amber-500 font-medium">Linked to {conv.linked_project_name}</div>
                {:else if conv.linked_to_current_project}
                  <div class="text-[10px] text-emerald-400 font-medium">Linked to current project</div>
                {/if}
              </div>
              <div class="flex items-center gap-3">
                <div class="text-right text-[9px] font-mono text-slate-400 space-y-1">
                  {#if conv.source}
                    <span class="px-1.5 py-0.5 rounded bg-sky-950/40 text-sky-400 border border-sky-900/30">{conv.source}</span>
                  {/if}
                  {#if conv.last_seen && conv.last_seen !== 'Active'}
                    <div class="text-[8px] text-slate-500 mt-1">seen: {conv.last_seen}</div>
                  {/if}
                </div>
                {#if conv.linked_to_other_project || conv.linked_to_current_project}
                  <button
                    type="button"
                    on:click|stopPropagation={() => triggerUnlink(conv, true)}
                    class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-2.5 py-1 text-xs font-semibold text-rose-400 hover:bg-rose-500 hover:text-white transition-colors"
                  >
                    Unlink
                  </button>
                {/if}
              </div>
            </div>
          {/each}
        </div>

        <div class="flex justify-end pt-2">
          <button
            on:click={handleLinkChatId}
            disabled={!selectedChatId || !selectedProject || !!(conversations.find(c => c.chat_id === selectedChatId)?.linked_to_other_project || conversations.find(c => c.chat_id === selectedChatId)?.linked_to_current_project)}
            class="bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 px-4 py-2 rounded-xl font-bold text-xs shadow transition-all border border-emerald-400 shrink-0"
          >
            Link Selected Conversation
          </button>
        </div>
      </div>
    {/if}

    {#if linkStatusLog}
      <div class="p-3 bg-slate-900 border border-slate-700/80 rounded-xl font-mono text-xs text-sky-300">
        {linkStatusLog}
      </div>
    {/if}
  </div>
</div>

{#if showUnlinkConfirm && unlinkTargetConv}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-6">
    <section
      role="dialog"
      aria-modal="true"
      aria-labelledby="unlink-conversation-title"
      class="w-full max-w-md rounded-xl border border-rose-500/30 bg-slate-900 p-5 shadow-2xl"
    >
      <div class="space-y-4">
        <div class="space-y-2">
          <h2 id="unlink-conversation-title" class="text-sm font-bold text-slate-100">Unlink Conversation</h2>
          <p class="text-xs leading-5 text-slate-400">
            Are you sure you want to unlink the Telegram conversation <span class="font-semibold text-slate-200">{unlinkTargetConv.title}</span>?
          </p>
          {#if unlinkTargetConv.linked_to_other_project}
            <p class="text-xs text-amber-400">
              This conversation is currently linked to project: <span class="font-semibold">{unlinkTargetConv.linked_project_name}</span>.
            </p>
          {:else if unlinkTargetConv.linked_to_current_project}
            <p class="text-xs text-emerald-400">
              This conversation is currently linked to the current project.
            </p>
          {/if}
          <div class="text-[10px] text-slate-500 font-mono">Chat ID: {unlinkTargetConv.chat_id}</div>
        </div>

        <div class="flex justify-end gap-2">
          <button
            type="button"
            on:click={cancelUnlink}
            class="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700"
          >
            Cancel
          </button>
          <button
            type="button"
            on:click={confirmUnlink}
            class="rounded-lg border border-rose-400 bg-rose-500 px-4 py-2 text-xs font-bold text-white hover:bg-rose-400"
          >
            Unlink
          </button>
        </div>
      </div>
    </section>
  </div>
{/if}
