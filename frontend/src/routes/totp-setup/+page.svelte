<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api, ApiError } from '$lib/api';
  import { setSession } from '$lib/stores/session';

  let secret = $state<string | null>(null);
  let code = $state('');
  let submitting = $state(false);
  let error = $state<string | null>(null);
  let loadError = $state<string | null>(null);

  onMount(async () => {
    try {
      const data = await api.post<{ secret: string; otpauth_uri: string }>('/auth/totp/enroll/');
      secret = data.secret;
    } catch {
      loadError = 'Failed to start TOTP enrollment. Please sign in again.';
    }
  });

  async function handleConfirm(e: SubmitEvent) {
    e.preventDefault();
    submitting = true;
    error = null;
    try {
      await api.post('/auth/totp/confirm/', { totp_token: code });
      // Session is now fully verified; fetch /me to hydrate
      const me = await api.get<{ user: any; household: any }>('/auth/me/');
      setSession({ user: me.user, household: me.household, totp_verified: true });
      await goto('/');
    } catch (err) {
      error =
        err instanceof ApiError ? ((err.body?.detail as string) ?? 'Invalid code.') : 'Error.';
    } finally {
      submitting = false;
    }
  }
</script>

<div class="flex min-h-screen items-center justify-center px-4 py-16 bg-surface-0">
  <div class="w-full max-w-sm">
    <!-- Logo -->
    <div class="mb-8 text-center">
      <h1 class="font-display text-3xl font-bold text-ink-primary tracking-tight">BudgetApp</h1>
      <p class="mt-1 text-sm text-ink-secondary">Household Finance</p>
    </div>

    <!-- Card -->
    <div class="card px-6 py-7 shadow-elevated">
      <h2 class="text-base font-semibold text-ink-primary mb-1">
        Set up two-factor authentication
      </h2>
      <p class="text-sm text-ink-secondary mb-5">
        TOTP is mandatory for all users. Scan the secret into your authenticator app, then confirm
        with a code.
      </p>

      {#if loadError}
        <p
          class="rounded border border-negative/30 bg-negative/10 px-3 py-2 text-sm text-negative mb-4"
          role="alert"
        >
          {loadError}
        </p>
        <a href="/login" class="btn-primary w-full block text-center">Back to sign in</a>
      {:else if secret === null}
        <p class="text-sm text-ink-muted text-center py-4">Loading enrollment data…</p>
      {:else}
        <!-- Secret display -->
        <div class="mb-5">
          <p class="label mb-1">Enter this secret into your authenticator app</p>
          <div class="rounded border border-surface-3 bg-surface-2 px-3 py-3">
            <code class="num text-sm font-medium text-ink-primary break-all tracking-wider">
              {secret}
            </code>
          </div>
          <p class="mt-2 text-[11px] text-ink-muted">
            Open Google Authenticator, Authy, or any TOTP app. Choose "Enter setup key" and paste
            the secret above. Time-based (TOTP) mode, 6 digits.
          </p>
        </div>

        <!-- Confirmation form -->
        <form class="space-y-4" onsubmit={handleConfirm} novalidate>
          <div>
            <label for="code" class="label">
              Confirmation code
              <span class="ml-1 text-ink-muted font-normal">(from your app)</span>
            </label>
            <input
              id="code"
              type="text"
              inputmode="numeric"
              pattern="[0-9]{6}"
              autocomplete="one-time-code"
              class="input num text-center text-lg tracking-[0.35em]"
              placeholder="000000"
              maxlength={6}
              bind:value={code}
              required
              disabled={submitting}
            />
          </div>

          {#if error}
            <p
              class="rounded border border-negative/30 bg-negative/10 px-3 py-2 text-sm text-negative"
              role="alert"
            >
              {error}
            </p>
          {/if}

          <button
            type="submit"
            class="btn-primary w-full mt-2"
            disabled={submitting || code.length !== 6}
          >
            {submitting ? 'Verifying…' : 'Confirm and continue'}
          </button>
        </form>
      {/if}
    </div>

    <p class="mt-6 text-center text-xs text-ink-muted">
      Self-hosted · Proprietary · All rights reserved
    </p>
  </div>
</div>
