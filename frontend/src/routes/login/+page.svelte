<script lang="ts">
  // TODO: wire to /api/v1/auth/... (password + mandatory TOTP per SPEC section 7.1).
  // This is a placeholder form only; it does not submit to the backend yet.
  let email = $state('');
  let password = $state('');
  let totp = $state('');
  let submitting = $state(false);
  let error = $state<string | null>(null);

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    submitting = true;
    error = 'Login is not wired up yet. TODO: call the DRF auth endpoints.';
    submitting = false;
  }
</script>

<section class="mx-auto max-w-sm space-y-4">
  <h1 class="text-2xl font-semibold tracking-tight">Sign in</h1>
  <p class="text-sm text-slate-600">
    TOTP is required for every user from day one (SPEC section 7.1).
  </p>

  <form class="space-y-3" onsubmit={handleSubmit}>
    <label class="block text-sm">
      <span class="mb-1 block font-medium">Email</span>
      <input
        type="email"
        autocomplete="username"
        class="w-full rounded border border-slate-300 px-2 py-1"
        bind:value={email}
        required
      />
    </label>

    <label class="block text-sm">
      <span class="mb-1 block font-medium">Password</span>
      <input
        type="password"
        autocomplete="current-password"
        class="w-full rounded border border-slate-300 px-2 py-1"
        bind:value={password}
        required
      />
    </label>

    <label class="block text-sm">
      <span class="mb-1 block font-medium">TOTP code</span>
      <input
        type="text"
        inputmode="numeric"
        pattern="[0-9]{6}"
        autocomplete="one-time-code"
        class="w-full rounded border border-slate-300 px-2 py-1"
        bind:value={totp}
        required
      />
    </label>

    <button
      type="submit"
      class="w-full rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
      disabled={submitting}
    >
      {submitting ? 'Signing in...' : 'Sign in'}
    </button>

    {#if error}
      <p class="text-sm text-red-700" role="alert">{error}</p>
    {/if}
  </form>
</section>
