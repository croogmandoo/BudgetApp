<script lang="ts">
  import '../app.css';

  interface Props {
    children?: import('svelte').Snippet;
  }

  const { children }: Props = $props();

  const navLinks = [
    { href: '/', label: 'Dashboard' },
    { href: '/transactions', label: 'Transactions' },
    { href: '/budgets', label: 'Budgets' },
    { href: '/bills', label: 'Bills' },
    { href: '/projects', label: 'Projects' },
    { href: '/maintenance', label: 'Maintenance' }
  ];
</script>

<div class="min-h-screen flex flex-col bg-slate-50 text-slate-900">
  <header class="border-b border-slate-200 bg-white">
    <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
      <a href="/" class="text-lg font-semibold tracking-tight">BudgetApp</a>
      <ul class="flex gap-4 text-sm">
        {#each navLinks as link (link.href)}
          <li>
            <a class="hover:underline" href={link.href}>{link.label}</a>
          </li>
        {/each}
      </ul>
      <a href="/login" class="text-sm hover:underline">Sign in</a>
    </nav>
  </header>

  <main class="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
    {@render children?.()}
  </main>

  <footer class="border-t border-slate-200 bg-white">
    <div class="mx-auto max-w-6xl px-4 py-3 text-xs text-slate-500">
      BudgetApp &mdash; self-hosted household finance. Proprietary, all rights reserved.
    </div>
  </footer>
</div>
