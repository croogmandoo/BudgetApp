<script lang="ts">
  import { api, ApiError } from '$lib/api';
  import type {
    Account,
    ImportConfirmResult,
    ImportPreviewResult,
    ImportProfile,
    ImportRow,
  } from '$lib/types';

  type Step = 'setup' | 'preview' | 'done';
  type Tab = 'import' | 'dupes' | 'errors';

  let accounts = $state<Account[]>([]);
  let profiles = $state<ImportProfile[]>([]);
  let accountId = $state('');
  let profileId = $state('');
  let file = $state<File | null>(null);
  let fileSha256 = $state('');
  let step = $state<Step>('setup');
  let activeTab = $state<Tab>('import');
  let preview = $state<ImportPreviewResult | null>(null);
  let result = $state<ImportConfirmResult | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let dragging = $state(false);

  $effect(() => {
    Promise.all([
      api.get<{ results: Account[] }>('/finances/accounts/'),
      api.get<{ results: ImportProfile[] }>('/finances/import-profiles/'),
    ])
      .then(([accs, profs]) => {
        accounts = accs.results;
        profiles = profs.results;
      })
      .catch(() => {
        error = 'Failed to load accounts or profiles.';
      });
  });

  async function sha256hex(f: File): Promise<string> {
    const buf = await f.arrayBuffer();
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  }

  async function handlePreview() {
    if (!accountId || !profileId || !file) return;
    loading = true;
    error = null;
    try {
      const form = new FormData();
      form.append('account_id', accountId);
      form.append('profile_id', profileId);
      form.append('file', file);
      const [sha, data] = await Promise.all([
        sha256hex(file),
        api.post<ImportPreviewResult>('/finances/imports/preview/', form),
      ]);
      fileSha256 = sha;
      preview = data;
      activeTab =
        data.to_import.length > 0 ? 'import' : data.probable_duplicates.length > 0 ? 'dupes' : 'errors';
      step = 'preview';
    } catch (err) {
      error = err instanceof ApiError ? err.message : 'Preview failed — check the file format.';
    } finally {
      loading = false;
    }
  }

  async function handleConfirm() {
    if (!preview || !accountId || !profileId) return;
    loading = true;
    error = null;
    try {
      const data = await api.post<ImportConfirmResult>('/finances/imports/confirm/', {
        account_id: accountId,
        profile_id: profileId,
        filename: file?.name ?? '',
        file_sha256: fileSha256,
        transactions: preview.to_import,
      });
      result = data;
      step = 'done';
    } catch (err) {
      error = err instanceof ApiError ? err.message : 'Import failed.';
    } finally {
      loading = false;
    }
  }

  function reset() {
    step = 'setup';
    preview = null;
    result = null;
    file = null;
    fileSha256 = '';
    error = null;
  }

  function pickFile(f: File) {
    file = f;
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    dragging = false;
    const f = e.dataTransfer?.files[0];
    if (f) pickFile(f);
  }

  function fmtAmount(a: string) {
    const n = parseFloat(a);
    const abs = Math.abs(n).toFixed(2);
    return n < 0 ? `−$${abs}` : `+$${abs}`;
  }

  function amountClass(a: string) {
    return parseFloat(a) < 0 ? 'num-neg' : 'num-pos';
  }

  let dupesCount = $derived((preview?.exact_duplicates.length ?? 0) + (preview?.probable_duplicates.length ?? 0));
</script>

<div class="px-5 py-6 space-y-6 max-w-3xl">
  <!-- Header -->
  <div class="flex items-end justify-between">
    <div>
      <h1 class="font-display text-2xl font-semibold text-ink-primary tracking-tight">
        Import Transactions
      </h1>
      {#if step === 'preview' && preview}
        <p class="text-sm text-ink-secondary mt-0.5">
          {preview.profile_name} · {file?.name}
        </p>
      {/if}
    </div>
    {#if step !== 'setup'}
      <button class="btn-ghost text-xs px-3 py-1.5" onclick={reset}>Start over</button>
    {/if}
  </div>

  <!-- ── Step 1: Setup ── -->
  {#if step === 'setup'}
    <div class="card px-5 py-5 space-y-5">
      <div>
        <label for="account" class="label">Account</label>
        <select id="account" class="input" bind:value={accountId} disabled={loading}>
          <option value="">Select account…</option>
          {#each accounts as a}
            <option value={a.id}>{a.name}{a.institution ? ` · ${a.institution}` : ''}</option>
          {/each}
        </select>
      </div>

      <div>
        <label for="profile" class="label">Bank profile</label>
        <select id="profile" class="input" bind:value={profileId} disabled={loading}>
          <option value="">Select bank…</option>
          {#each profiles as p}
            <option value={p.id}>{p.institution} ({p.format.toUpperCase()})</option>
          {/each}
        </select>
      </div>

      <div>
        <label for="file-input" class="label">File</label>
        <!-- svelte-ignore a11y_interactive_supports_focus -->
        <div
          class="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-150
            {dragging ? 'border-accent bg-accent/5' : 'border-surface-3 hover:border-accent/60'}"
          role="button"
          ondragover={(e) => { e.preventDefault(); dragging = true; }}
          ondragleave={() => { dragging = false; }}
          ondrop={onDrop}
          onclick={() => (document.getElementById('file-input') as HTMLInputElement)?.click()}
          onkeydown={(e) => e.key === 'Enter' && (document.getElementById('file-input') as HTMLInputElement)?.click()}
        >
          {#if file}
            <p class="text-sm font-medium text-ink-primary">{file.name}</p>
            <p class="text-xs text-ink-muted mt-1">{(file.size / 1024).toFixed(1)} KB · click to change</p>
          {:else}
            <p class="text-sm text-ink-secondary">Drop file here or <span class="text-accent">browse</span></p>
            <p class="text-xs text-ink-muted mt-1">CSV, XLS, XLSX — max 10 MB</p>
          {/if}
        </div>
        <input
          id="file-input"
          type="file"
          accept=".csv,.xls,.xlsx"
          class="hidden"
          onchange={(e) => {
            const f = (e.currentTarget as HTMLInputElement).files?.[0];
            if (f) pickFile(f);
          }}
        />
      </div>

      {#if error}
        <p class="rounded border border-negative/30 bg-negative/10 px-3 py-2 text-sm text-negative" role="alert">
          {error}
        </p>
      {/if}

      <button
        class="btn-primary"
        onclick={handlePreview}
        disabled={!accountId || !profileId || !file || loading}
      >
        {loading ? 'Parsing…' : 'Preview Import'}
      </button>
    </div>
  {/if}

  <!-- ── Step 2: Preview ── -->
  {#if step === 'preview' && preview}
    <!-- Summary strip -->
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {#each [
        { label: 'To import', value: preview.to_import.length, accent: true },
        { label: 'Exact duplicates', value: preview.exact_duplicates.length },
        { label: 'Probable duplicates', value: preview.probable_duplicates.length },
        { label: 'Parse errors', value: preview.parse_errors.length, warn: preview.parse_errors.length > 0 },
      ] as stat}
        <div class="card px-4 py-3">
          <p class="text-[11px] uppercase tracking-wider text-ink-secondary mb-1">{stat.label}</p>
          <p class="num text-xl font-medium {stat.accent ? 'text-accent' : stat.warn ? 'text-caution' : 'text-ink-primary'}">
            {stat.value}
          </p>
        </div>
      {/each}
    </div>

    <!-- Tab bar -->
    <div class="card overflow-hidden">
      <div class="flex border-b border-surface-3">
        {#each [
          { id: 'import' as Tab, label: `To Import (${preview.to_import.length})` },
          { id: 'dupes' as Tab, label: `Duplicates (${dupesCount})` },
          { id: 'errors' as Tab, label: `Errors (${preview.parse_errors.length})` },
        ] as tab}
          <button
            class="px-4 py-2.5 text-sm font-medium transition-colors duration-100
              {activeTab === tab.id
                ? 'border-b-2 border-accent text-accent'
                : 'text-ink-secondary hover:text-ink-primary'}"
            onclick={() => (activeTab = tab.id)}
          >
            {tab.label}
          </button>
        {/each}
      </div>

      <!-- To Import table -->
      {#if activeTab === 'import'}
        {#if preview.to_import.length === 0}
          <p class="px-5 py-8 text-center text-sm text-ink-muted">No new transactions to import.</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-surface-3">
                  {#each ['Date', 'Payee', 'Memo', 'Amount'] as col, i}
                    <th class="px-4 py-2 text-[11px] font-medium uppercase tracking-wider text-ink-muted
                      {i === 3 ? 'text-right' : 'text-left'}
                      {i === 2 ? 'hidden sm:table-cell' : ''}">{col}</th>
                  {/each}
                </tr>
              </thead>
              <tbody>
                {#each preview.to_import as row}
                  <tr class="border-b border-surface-3/50 last:border-0 hover:bg-surface-2 transition-colors duration-100">
                    <td class="px-4 py-2.5 num text-[12px] text-ink-muted whitespace-nowrap">{row.date}</td>
                    <td class="px-4 py-2.5 text-ink-primary font-medium">{row.payee || '—'}</td>
                    <td class="hidden sm:table-cell px-4 py-2.5 text-ink-secondary text-xs truncate max-w-[200px]">{row.memo || '—'}</td>
                    <td class="px-4 py-2.5 text-right">
                      <span class="{amountClass(row.amount)}">{fmtAmount(row.amount)}</span>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {/if}

      <!-- Duplicates table -->
      {#if activeTab === 'dupes'}
        {#if dupesCount === 0}
          <p class="px-5 py-8 text-center text-sm text-ink-muted">No duplicates detected.</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-surface-3">
                  {#each ['Date', 'Payee', 'Amount', 'Reason'] as col, i}
                    <th class="px-4 py-2 text-[11px] font-medium uppercase tracking-wider text-ink-muted
                      {i === 2 ? 'text-right' : 'text-left'}
                      {i === 3 ? 'hidden sm:table-cell' : ''}">{col}</th>
                  {/each}
                </tr>
              </thead>
              <tbody>
                {#each preview.exact_duplicates as row}
                  <tr class="border-b border-surface-3/50 last:border-0">
                    <td class="px-4 py-2.5 num text-[12px] text-ink-muted whitespace-nowrap">{row.date}</td>
                    <td class="px-4 py-2.5 text-ink-secondary">{row.payee || '—'}</td>
                    <td class="px-4 py-2.5 text-right"><span class="{amountClass(row.amount)}">{fmtAmount(row.amount)}</span></td>
                    <td class="hidden sm:table-cell px-4 py-2.5"><span class="pill bg-surface-3 text-ink-muted">Exact match</span></td>
                  </tr>
                {/each}
                {#each preview.probable_duplicates as row}
                  <tr class="border-b border-surface-3/50 last:border-0">
                    <td class="px-4 py-2.5 num text-[12px] text-ink-muted whitespace-nowrap">{row.date}</td>
                    <td class="px-4 py-2.5 text-ink-secondary">{row.payee || '—'}</td>
                    <td class="px-4 py-2.5 text-right"><span class="{amountClass(row.amount)}">{fmtAmount(row.amount)}</span></td>
                    <td class="hidden sm:table-cell px-4 py-2.5"><span class="pill bg-caution/10 text-caution">{row.match_reason}</span></td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {/if}

      <!-- Errors table -->
      {#if activeTab === 'errors'}
        {#if preview.parse_errors.length === 0}
          <p class="px-5 py-8 text-center text-sm text-ink-muted">No parse errors.</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-surface-3">
                  <th class="px-4 py-2 text-[11px] font-medium uppercase tracking-wider text-ink-muted text-left">Row</th>
                  <th class="px-4 py-2 text-[11px] font-medium uppercase tracking-wider text-ink-muted text-left">Reason</th>
                </tr>
              </thead>
              <tbody>
                {#each preview.parse_errors as err}
                  <tr class="border-b border-surface-3/50 last:border-0">
                    <td class="px-4 py-2.5 num text-[12px] text-ink-muted">{err.row}</td>
                    <td class="px-4 py-2.5 text-negative text-xs">{err.reason}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {/if}
    </div>

    {#if error}
      <p class="rounded border border-negative/30 bg-negative/10 px-3 py-2 text-sm text-negative" role="alert">
        {error}
      </p>
    {/if}

    <div class="flex items-center gap-3">
      <button
        class="btn-primary"
        onclick={handleConfirm}
        disabled={!preview.to_import.length || loading}
      >
        {loading ? 'Importing…' : `Import ${preview.to_import.length} transaction${preview.to_import.length === 1 ? '' : 's'}`}
      </button>
      <button class="btn-ghost" onclick={reset}>Cancel</button>
    </div>
  {/if}

  <!-- ── Step 3: Done ── -->
  {#if step === 'done' && result}
    <div class="card px-6 py-8 text-center space-y-4">
      <div class="text-4xl">✓</div>
      <h2 class="font-display text-xl font-semibold text-ink-primary">Import complete</h2>
      <div class="grid grid-cols-3 gap-4 max-w-sm mx-auto mt-4">
        <div>
          <p class="num text-2xl font-medium text-accent">{result.imported}</p>
          <p class="text-xs text-ink-muted mt-0.5">imported</p>
        </div>
        <div>
          <p class="num text-2xl font-medium text-ink-primary">{result.rules_applied}</p>
          <p class="text-xs text-ink-muted mt-0.5">rules applied</p>
        </div>
        <div>
          <p class="num text-2xl font-medium text-ink-secondary">{result.skipped_duplicates}</p>
          <p class="text-xs text-ink-muted mt-0.5">skipped</p>
        </div>
      </div>
      <div class="flex items-center justify-center gap-3 pt-2">
        <button class="btn-primary" onclick={reset}>Import another file</button>
        <a href="/transactions" class="btn-ghost">View transactions</a>
      </div>
    </div>
  {/if}
</div>
