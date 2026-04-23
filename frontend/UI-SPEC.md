# BudgetApp — UI Design Specification

## Design Direction: Warm Ledger

**Concept:** A personal finance tool that feels like a beautifully maintained accounting ledger — warm, precise, trustworthy. Not cold fintech. Not startup SaaS. Something a careful person built for themselves and their household.

**Tone:** Trustworthy, data-dense without being overwhelming, quietly refined. Numbers are the star — the UI frames them without competing.

**What makes it distinctive:** Monospaced numbers creating natural columns; a warm dark palette (not cold gray) that feels premium and readable at night; a serif display font that brings editorial warmth to financial data.

---

## Color Tokens

All colors are defined as Tailwind theme extensions and CSS custom properties.

| Token           | Hex       | Usage                                              |
| --------------- | --------- | -------------------------------------------------- |
| `surface-0`     | `#111210` | Page background                                    |
| `surface-1`     | `#1a1918` | Sidebar, cards, panels                             |
| `surface-2`     | `#242220` | Hover states, input backgrounds, elevated surfaces |
| `surface-3`     | `#302e2b` | Borders, dividers, separators                      |
| `ink-primary`   | `#f2ede4` | Primary text (headings, values)                    |
| `ink-secondary` | `#9a9389` | Secondary text, labels, placeholders               |
| `ink-muted`     | `#5a5650` | Disabled state, very subtle text                   |
| `accent`        | `#c9a84c` | Brand gold — active nav, links, focus rings        |
| `positive`      | `#5bbf8a` | Income, positive balances, success states          |
| `negative`      | `#d9594c` | Expenses, overspent envelopes, error states        |
| `caution`       | `#d4903a` | Due soon, nearly empty envelopes, warnings         |
| `info`          | `#6b9fca` | Neutral informational, pending states              |

### Semantic Usage Rules

- `positive` / `negative` / `caution` on **numbers only** (amounts, balances). Never on UI chrome.
- `accent` on interactive focus states, active nav indicator, primary buttons. Use sparingly — it should feel like a highlight, not wallpaper.
- `surface-0` for the page. `surface-1` for sidebar and main cards. `surface-2` for nested/elevated elements (row hover, open dropdowns, input fields).
- Never use raw white (`#fff`) or raw black (`#000`). The warm tones are intentional.

---

## Typography

| Role    | Font           | Weight  | Size            | Usage                                                 |
| ------- | -------------- | ------- | --------------- | ----------------------------------------------------- |
| Display | Fraunces       | 700     | 1.75rem–3rem    | Page headings, net worth, big numbers                 |
| Heading | Fraunces       | 600     | 1.125rem–1.5rem | Section headings, card titles                         |
| Body    | DM Sans        | 400     | 0.875rem        | Body text, nav labels, descriptions                   |
| Label   | DM Sans        | 500–600 | 0.75rem         | Form labels, table headers, badges                    |
| Data    | JetBrains Mono | 400–500 | 0.8125rem–1rem  | **All currency amounts, dates in tables, codes, IDs** |

### Number Formatting Rules

- **All currency amounts** use `font-mono tabular-nums` — non-negotiable. Creates column alignment and prevents layout shift.
- Currency prefix (`$`) is always included in the same element as the number.
- Positive amounts: `text-positive` (green).
- Negative amounts / expenses: `text-negative` (terracotta). Amount is displayed as negative (e.g., `−$89.43`).
- Neutral / pending amounts: `text-ink-secondary`.
- Large hero numbers (net worth, monthly totals): `font-display` + `tabular-nums`.

### Tailwind Utility Classes

```
.num     — font-mono tabular-nums (neutral)
.num-pos — font-mono tabular-nums text-positive
.num-neg — font-mono tabular-nums text-negative
.num-warn— font-mono tabular-nums text-caution
```

---

## Spacing & Layout

| Breakpoint          | Layout                                                                              |
| ------------------- | ----------------------------------------------------------------------------------- |
| `< 768px` (mobile)  | No sidebar. Bottom tab bar (6 tabs). Full-width content. Top: page title + profile. |
| `≥ 768px` (tablet+) | Left sidebar 224px fixed. Main content: fluid, `min-w-0`.                           |

**Content max-width:** `max-w-4xl` (56rem) for page content inside the main area.
**Page padding:** `px-5 py-6` on desktop, `px-4 py-4` on mobile.
**Grid:** 12-column conceptually. Dashboard uses 4-column stat grid (collapse to 2 on mobile, 1 on smallest).
**Card gap:** `gap-4`.
**Section spacing:** `space-y-6` between major page sections.

---

## Navigation

### Sidebar (≥ md)

```
┌──────────────┐
│  BudgetApp   │  ← font-display, 18px
│  Household   │  ← ink-secondary, 11px
├──────────────┤
│  To budget   │  ← surface-2 banner, accent number
│  $842.33     │
├──────────────┤
│ ▌ Dashboard  │  ← active: surface-2 bg + accent left border (2px)
│   Transact.  │
│   Budgets    │  ← inactive: ink-secondary, hover: surface-2
│   Bills      │
│   Projects   │
│   Maintenanc.│
├──────────────┤
│   Settings   │
│ C  craig@… │  ← avatar initial + truncated email
└──────────────┘
```

- Active state: `bg-surface-2` + a `2px` `bg-accent` left-edge strip, `text-ink-primary`.
- Hover: `bg-surface-2`, `text-ink-primary`, 150ms transition.
- Icons: 16px stroke SVGs, `stroke-width: 1.75`.

### Bottom Nav (< md)

- Fixed to bottom edge, `bg-surface-1 border-t border-surface-3`, `z-50`.
- 6 equal-width tabs: icon (20px) + truncated label (10px DM Sans).
- Active: `text-accent`. Inactive: `text-ink-muted`.
- Mobile content area has `pb-20` to clear the nav.

---

## Component Patterns

### Stat Card

```
┌─────────────────┐
│ Income          │  ← label: 11px, ink-secondary
│ $8,450.00       │  ← value: 22px, font-display/font-mono, ink-primary
│ ▲ +$200 vs last │  ← trend: 11px, positive/negative color
└─────────────────┘
```

- Background: `surface-1`. Border: `surface-3`. Rounded: `rounded-lg`.
- Four per row on desktop (gap-4). Two per row on mobile.

### Transaction Row (table)

```
Apr 22  │ Whole Foods Market      │ Groceries   │ −$89.43
```

- `<table>` or CSS grid. Four columns: Date | Payee | Category | Amount.
- Date: `num text-ink-secondary`, `w-20`, right-padded.
- Payee: `text-ink-primary font-medium`, `flex-1`.
- Category: pill badge, `surface-2` bg, `ink-secondary` text, `text-xs rounded-full px-2 py-0.5`.
- Amount: `num-neg` or `num-pos`, `text-right w-24`, always right-aligned.
- Row hover: `bg-surface-2` transition 120ms.
- Uncategorized: pill in `caution/20` bg, `text-caution`.
- Pending: `text-ink-muted italic` on payee.

### Envelope Bar

```
Groceries        $234 / $400       ████████░░░░  58%
```

- Category name left, amount right, bar below.
- Bar fill: green < 80%, amber 80–99%, red ≥ 100%.
- Bar track: `surface-3`. Height: `3px`. Rounded full.

### Bill Card (compact)

```
┌──────────────────────────────┐
│ Mortgage          $2,150.00  │
│ Due Apr 25     ● Upcoming    │
└──────────────────────────────┘
```

- Status dot + label: green=Paid, amber=Upcoming, red=Overdue.
- Overdue: `negative/10` background tint.

### Form Input

```css
background: surface-2
border: 1px solid surface-3
border-radius: 6px
padding: 8px 12px
color: ink-primary
font: DM Sans 14px

focus:
  border-color: accent
  outline: 2px solid accent/30
```

- Error state: `border-negative`, error message in `text-negative text-xs` below.
- Label: `text-xs font-medium text-ink-secondary mb-1`.

### Primary Button

```css
background: accent
color: surface-0
font: DM Sans 14px font-medium
padding: 10px 20px
border-radius: 6px
transition: opacity 150ms

hover: opacity-90
active: opacity-80
disabled: opacity-40 cursor-not-allowed
```

### Ghost Button

```css
background: transparent
border: 1px solid surface-3
color: ink-secondary
```

Same sizing as primary. Hover: `surface-2` bg.

### Badge / Pill

```
rounded-full px-2 py-0.5 text-xs font-medium
```

Colors: use semantic `*-bg` colors from color tokens (e.g., `positive/10` bg + `positive` text).

---

## Page Structure

### Dashboard

```
[Page title + month selector]
[4 stat cards: Income | Spent | To Budget | Bills Due]
[2-col grid on desktop / stacked on mobile]
  Left: Recent Transactions (table, last 10)
  Right: Upcoming Bills (list, next 5)
[Quick action row: Import, Add Transaction, Budget]
```

### Transactions

```
[Filter bar: account, category, date range, search]
[Transactions table — full width]
[Pagination or infinite scroll]
```

### Budgets

```
[Period selector (month)]
[To-be-budgeted banner]
[Envelope groups by category (hierarchical)]
```

### Bills

```
[Month calendar strip]
[Bill instances: grouped by status]
```

### Projects / Maintenance

```
[Card grid — project/task cards]
```

---

## Motion

**Principle:** Intentional and restrained. Every animation serves communication.

| Element                   | Animation                     | Duration / Easing |
| ------------------------- | ----------------------------- | ----------------- |
| Page transition           | Fade + 6px slide up           | 200ms ease-out    |
| Row hover                 | Background color              | 120ms ease        |
| Number update             | Count-up (JS) on first render | 400ms ease-out    |
| Sidebar collapse (future) | Width + opacity               | 200ms ease-in-out |
| Form error                | Shake                         | 200ms             |
| Toast/notification        | Slide in from right           | 250ms spring      |

No bounce, no spring physics on structural elements. Micro-interactions only on data reveals and user feedback moments.

---

## Accessibility

- Keyboard navigation: all interactive elements reachable with Tab. Focus ring: `outline: 2px solid accent` with `2px offset`.
- Color is never the only signal — use text labels alongside color coding (e.g., "Overdue" label, not just red text).
- ARIA labels on icon-only buttons.
- Table data cells use `role="cell"`, headers `scope="col"`.
- `prefers-reduced-motion`: disable count-up and page transition animations.
- Minimum contrast ratio: 4.5:1 for body text, 3:1 for large text. `ink-primary` on `surface-1` passes comfortably.

---

## File Conventions

- `src/routes/` — pages follow SvelteKit conventions.
- `src/lib/components/` — shared components. Name by pattern: `StatCard.svelte`, `TransactionRow.svelte`, etc.
- Tailwind utilities for one-off styles; shared patterns go in `@layer components` in `app.css`.
- CSS custom properties (`--surface-0`, etc.) are defined in `:root` for use in inline styles when Tailwind class isn't available.
