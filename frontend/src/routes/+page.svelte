<script lang="ts">
  // Dashboard — placeholder data until the API is wired.
  // Real data will come from /api/v1/ once auth and models are live.

  const stats = [
    { label: 'Income', value: '$8,450.00', trend: '+$200', up: true },
    { label: 'Spent', value: '$4,217.32', trend: '−$312 vs last', up: false },
    { label: 'To Budget', value: '$842.33', accent: true },
    { label: 'Bills Due', value: '3', sub: 'this week', warn: true }
  ];

  const transactions = [
    {
      date: 'Apr 22',
      payee: 'Whole Foods Market',
      category: 'Groceries',
      amount: '−$89.43',
      neg: true
    },
    { date: 'Apr 21', payee: 'Netflix', category: 'Streaming', amount: '−$22.99', neg: true },
    { date: 'Apr 20', payee: 'CIBC Payroll', category: 'Income', amount: '+$4,225.00', pos: true },
    {
      date: 'Apr 19',
      payee: 'Shell Gas Station',
      category: 'Auto · Fuel',
      amount: '−$67.80',
      neg: true
    },
    { date: 'Apr 18', payee: 'Rogers Wireless', category: 'Phone', amount: '−$95.00', neg: true },
    {
      date: 'Apr 17',
      payee: 'LCBO',
      category: null,
      amount: '−$34.50',
      neg: true,
      uncategorized: true
    },
    { date: 'Apr 16', payee: 'Amazon.ca', category: 'Shopping', amount: '−$127.94', neg: true }
  ];

  const bills = [
    { name: 'Mortgage', amount: '$2,150.00', due: 'Apr 25', status: 'upcoming' },
    { name: 'Hydro One', amount: '$142.50', due: 'Apr 28', status: 'upcoming' },
    { name: 'Rogers Internet', amount: '$89.99', due: 'May 1', status: 'upcoming' },
    { name: 'Car Insurance', amount: '$218.00', due: 'Apr 15', status: 'paid' }
  ];

  const statusColor: Record<string, string> = {
    paid: 'text-positive',
    upcoming: 'text-caution',
    overdue: 'text-negative'
  };
  const statusDot: Record<string, string> = {
    paid: 'bg-positive',
    upcoming: 'bg-caution',
    overdue: 'bg-negative'
  };
</script>

<div class="px-5 py-6 space-y-6 max-w-4xl">
  <!-- ── Page header ── -->
  <div class="flex items-end justify-between">
    <div>
      <h1 class="font-display text-2xl font-semibold text-ink-primary tracking-tight">Dashboard</h1>
      <p class="text-sm text-ink-secondary mt-0.5">April 2026</p>
    </div>
    <div class="flex items-center gap-2">
      <a href="/import" class="btn-ghost text-xs px-3 py-1.5">Import</a>
      <button class="btn-primary text-xs px-3 py-1.5">+ Transaction</button>
    </div>
  </div>

  <!-- ── Net worth hero ── -->
  <div class="card px-5 py-4">
    <p class="text-xs text-ink-secondary uppercase tracking-wider mb-1">Net Worth</p>
    <div class="flex items-baseline gap-3">
      <span class="font-display text-4xl font-bold text-ink-primary num">$47,823.44</span>
      <span class="text-sm text-positive num">▲ $832 this month</span>
    </div>
  </div>

  <!-- ── Stat cards ── -->
  <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
    {#each stats as s}
      <div class="card px-4 py-3">
        <p class="text-[11px] uppercase tracking-wider text-ink-secondary mb-1">{s.label}</p>
        <p
          class="num text-xl font-medium {s.accent
            ? 'text-accent'
            : s.warn
              ? 'text-caution'
              : 'text-ink-primary'}"
        >
          {s.value}
        </p>
        {#if s.trend}
          <p class="text-[11px] mt-0.5 num {s.up ? 'text-positive' : 'text-negative'}">{s.trend}</p>
        {/if}
        {#if s.sub}
          <p class="text-[11px] mt-0.5 text-ink-muted">{s.sub}</p>
        {/if}
      </div>
    {/each}
  </div>

  <!-- ── Two-column: transactions + bills ── -->
  <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
    <!-- Recent transactions (spans 2 of 3 cols) -->
    <div class="card lg:col-span-2">
      <div class="flex items-center justify-between border-b border-surface-3 px-4 py-3">
        <h2 class="text-sm font-semibold text-ink-primary">Recent Transactions</h2>
        <a href="/transactions" class="text-xs text-accent hover:underline">View all</a>
      </div>

      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-surface-3">
            <th
              class="px-4 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-ink-muted"
              >Date</th
            >
            <th
              class="px-4 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-ink-muted"
              >Payee</th
            >
            <th
              class="hidden px-4 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-ink-muted sm:table-cell"
              >Category</th
            >
            <th
              class="px-4 py-2 text-right text-[11px] font-medium uppercase tracking-wider text-ink-muted"
              >Amount</th
            >
          </tr>
        </thead>
        <tbody>
          {#each transactions as tx}
            <tr
              class="border-b border-surface-3/50 transition-colors duration-100 hover:bg-surface-2 last:border-0"
            >
              <td class="px-4 py-2.5 num text-[12px] text-ink-muted whitespace-nowrap">{tx.date}</td
              >
              <td class="px-4 py-2.5 text-ink-primary font-medium">{tx.payee}</td>
              <td class="hidden px-4 py-2.5 sm:table-cell">
                {#if tx.uncategorized}
                  <span class="pill bg-caution/10 text-caution">Uncategorized</span>
                {:else if tx.category}
                  <span class="pill bg-surface-3 text-ink-secondary">{tx.category}</span>
                {/if}
              </td>
              <td class="px-4 py-2.5 text-right">
                <span class="num text-[13px] {tx.pos ? 'num-pos' : tx.neg ? 'num-neg' : ''}"
                  >{tx.amount}</span
                >
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Upcoming bills (1 of 3 cols) -->
    <div class="card">
      <div class="flex items-center justify-between border-b border-surface-3 px-4 py-3">
        <h2 class="text-sm font-semibold text-ink-primary">Bills</h2>
        <a href="/bills" class="text-xs text-accent hover:underline">View all</a>
      </div>
      <ul class="divide-y divide-surface-3/50">
        {#each bills as bill}
          <li class="px-4 py-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="text-sm font-medium text-ink-primary truncate">{bill.name}</p>
                <p class="text-[11px] text-ink-muted mt-0.5">Due {bill.due}</p>
              </div>
              <p class="num text-sm text-ink-primary shrink-0">{bill.amount}</p>
            </div>
            <div class="mt-1.5 flex items-center gap-1.5">
              <span class="h-1.5 w-1.5 rounded-full {statusDot[bill.status]}"></span>
              <span class="text-[11px] capitalize {statusColor[bill.status]}">{bill.status}</span>
            </div>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</div>
