<script>
  const docsUrl = 'https://kyleit.github.io/AI-Agent-Workflow/';
  let frameKey = 0;

  function reloadDocs() {
    frameKey += 1;
  }
</script>

<div class="relative w-full h-full bg-slate-900">
  <button
    type="button"
    on:click={reloadDocs}
    title="Reload Documentation"
    aria-label="Reload Documentation"
    class="absolute top-3 right-3 z-10 flex h-8 w-8 items-center justify-center rounded-lg border border-slate-700 bg-slate-800/80 text-slate-300 backdrop-blur-sm shadow-md transition-all hover:bg-slate-700 hover:text-white active:scale-95"
  >
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
      <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
    </svg>
  </button>

  {#key frameKey}
    <iframe
      title="AIWF Documentation"
      src={docsUrl}
      class="w-full h-full border-0 bg-white"
      referrerpolicy="no-referrer"
    ></iframe>
  {/key}
</div>
