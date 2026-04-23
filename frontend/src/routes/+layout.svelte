<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
  import type { Snippet } from 'svelte';

  interface Props {
    children: Snippet;
  }

  const { children }: Props = $props();

  const AUTH_PATHS = ['/login', '/setup', '/totp-setup'];

  let isShell = $derived(!AUTH_PATHS.some((p) => $page.url.pathname.startsWith(p)));

  type NavItem = { href: string; label: string; icon: string; exact?: boolean };

  const nav: NavItem[] = [
    { href: '/', label: 'Dashboard', icon: 'home', exact: true },
    { href: '/transactions', label: 'Transactions', icon: 'arrows' },
    { href: '/budgets', label: 'Budgets', icon: 'wallet' },
    { href: '/bills', label: 'Bills', icon: 'calendar' },
    { href: '/projects', label: 'Projects', icon: 'wrench' },
    { href: '/maintenance', label: 'Maintenance', icon: 'bell' }
  ];

  function isActive(item: NavItem): boolean {
    const p = $page.url.pathname;
    if (item.exact) return p === item.href;
    return p === item.href || p.startsWith(item.href + '/');
  }

  // Stroke-based SVG paths (viewBox 0 0 24 24, fill none)
  const icons: Record<string, string> = {
    home: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM9 22V12h6v10',
    arrows: 'M8 3L4 7l4 4M4 7h16M16 21l4-4-4-4M20 17H4',
    wallet: 'M21 12V7H5a2 2 0 0 1 0-4h14v4M3 5v14a2 2 0 0 0 2 2h16v-5M18 12a2 2 0 0 0 0 4h4v-4z',
    calendar:
      'M8 7V3M16 7V3M3 11h18M5 21h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2z',
    wrench:
      'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z',
    bell: 'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0',
    settings:
      'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z'
  };
</script>

{#if !isShell}
  <div class="min-h-screen bg-surface-0">
    {@render children()}
  </div>
{:else}
  <div class="flex min-h-screen bg-surface-0">
    <!-- ── Sidebar (md+) ── -->
    <aside
      class="hidden md:flex md:w-56 md:shrink-0 md:flex-col bg-surface-1 border-r border-surface-3"
    >
      <!-- Logo -->
      <div class="px-5 pt-6 pb-4">
        <a
          href="/"
          class="text-lg font-display font-semibold text-ink-primary tracking-tight leading-none"
        >
          BudgetApp
        </a>
        <p class="mt-0.5 text-[11px] text-ink-muted uppercase tracking-widest">Household</p>
      </div>

      <!-- To-be-budgeted banner -->
      <div class="mx-3 mb-4 rounded border border-surface-3 bg-surface-2 px-3 py-2">
        <p class="text-[11px] text-ink-secondary">To budget</p>
        <p class="num text-base text-accent font-medium">$842.33</p>
        <p class="text-[11px] text-ink-muted">April 2026</p>
      </div>

      <!-- Primary nav -->
      <nav class="flex-1 px-2 space-y-0.5">
        {#each nav as item (item.href)}
          {@const active = isActive(item)}
          <a
            href={item.href}
            class="relative flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors duration-150
              {active
              ? 'bg-surface-2 text-ink-primary'
              : 'text-ink-secondary hover:bg-surface-2 hover:text-ink-primary'}"
          >
            {#if active}
              <span class="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r-full bg-accent"
              ></span>
            {/if}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="shrink-0"
              aria-hidden="true"
            >
              <path d={icons[item.icon]} />
            </svg>
            <span>{item.label}</span>
          </a>
        {/each}
      </nav>

      <!-- Sidebar footer -->
      <div class="border-t border-surface-3 px-2 py-3 space-y-0.5">
        <a
          href="/settings"
          class="flex items-center gap-3 rounded px-3 py-2 text-sm text-ink-secondary transition-colors duration-150 hover:bg-surface-2 hover:text-ink-primary"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="shrink-0"
            aria-hidden="true"
          >
            <path d={icons.settings} />
          </svg>
          <span>Settings</span>
        </a>
        <div class="flex items-center gap-3 px-3 py-2 text-sm">
          <span
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/20 text-[11px] font-semibold text-accent"
            >C</span
          >
          <span class="truncate text-xs text-ink-secondary">craig@household</span>
        </div>
      </div>
    </aside>

    <!-- ── Main content ── -->
    <main class="min-w-0 flex-1 pb-20 md:pb-0">
      {@render children()}
    </main>
  </div>

  <!-- ── Bottom nav (mobile only) ── -->
  <nav
    class="fixed bottom-0 left-0 right-0 z-50 flex border-t border-surface-3 bg-surface-1 md:hidden"
    aria-label="Main navigation"
  >
    {#each nav as item (item.href)}
      {@const active = isActive(item)}
      <a
        href={item.href}
        class="flex flex-1 flex-col items-center gap-1 py-2.5 transition-colors duration-150
          {active ? 'text-accent' : 'text-ink-muted'}"
        aria-current={active ? 'page' : undefined}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d={icons[item.icon]} />
        </svg>
        <span class="text-[10px] leading-none"
          >{item.label.length > 6 ? item.label.slice(0, 5) + '…' : item.label}</span
        >
      </a>
    {/each}
  </nav>
{/if}
