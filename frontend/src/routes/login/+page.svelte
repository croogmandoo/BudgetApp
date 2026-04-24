<script lang="ts">
  import { goto } from '$app/navigation';
  import { api, ApiError } from '$lib/api';
  import type { User, Household } from '$lib/types';
  import { setSession } from '$lib/stores/session';

  let email = $state('');
  let password = $state('');
  let totp = $state('');
  let submitting = $state(false);
  let error = $state<string | null>(null);

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    submitting = true;
    error = null;

    try {
      const data = await api.post<{
        totp_enrollment_required: boolean;
        user: User;
        household?: Household;
      }>('/auth/login/', { email, password, totp_token: totp });

      if (data.totp_enrollment_required) {
        // Partial session — go enroll TOTP
        await goto('/totp-setup');
      } else {
        setSession({ user: data.user, household: data.household!, totp_verified: true });
        await goto('/');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        error = (err.body?.detail as string) ?? 'Sign in failed. Please try again.';
      } else {
        error = 'An unexpected error occurred.';
      }
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
      <h2 class="text-base font-semibold text-ink-primary mb-5">Sign in to your household</h2>

      <form class="space-y-4" onsubmit={handleSubmit} novalidate>
        <div>
          <label for="email" class="label">Email address</label>
          <input
            id="email"
            type="email"
            autocomplete="username"
            class="input"
            placeholder="you@example.com"
            bind:value={email}
            required
            disabled={submitting}
          />
        </div>

        <div>
          <label for="password" class="label">Password</label>
          <input
            id="password"
            type="password"
            autocomplete="current-password"
            class="input"
            placeholder="••••••••"
            bind:value={password}
            required
            disabled={submitting}
          />
        </div>

        <div>
          <label for="totp" class="label">
            Authenticator code
            <span class="ml-1 text-ink-muted font-normal">(required)</span>
          </label>
          <input
            id="totp"
            type="text"
            inputmode="numeric"
            pattern="[0-9]{6}"
            autocomplete="one-time-code"
            class="input num text-center text-lg tracking-[0.35em]"
            placeholder="000000"
            maxlength={6}
            bind:value={totp}
            required
            disabled={submitting}
          />
          <p class="mt-1 text-[11px] text-ink-muted">
            6-digit code from your authenticator app. TOTP is mandatory for all users.
          </p>
        </div>

        {#if error}
          <p
            class="rounded border border-negative/30 bg-negative/10 px-3 py-2 text-sm text-negative"
            role="alert"
          >
            {error}
          </p>
        {/if}

        <button type="submit" class="btn-primary w-full mt-2" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>

    <p class="mt-6 text-center text-xs text-ink-muted">
      Self-hosted · Proprietary · All rights reserved
    </p>
  </div>
</div>
