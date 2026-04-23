/**
 * Hand-rolled TypeScript types mirroring the minimal shape of SPEC section 6.
 *
 * NOTE: these are placeholders. Once the Django + DRF backend ships its
 * OpenAPI 3.1 schema at `/api/schema` (SPEC section 5.1), these should be
 * replaced with generated types (e.g. via `openapi-typescript`). Keeping
 * them thin on purpose so drift before generation is cheap.
 */

export type UUID = string;
// ISO-8601 date (e.g. "2026-04-23").
export type ISODate = string;
// ISO-8601 datetime.
export type ISODateTime = string;
// Decimal-as-string to avoid JS float rounding (DRF default for DecimalField).
export type DecimalString = string;

export type Role = 'admin' | 'member' | 'viewer';

export type AccountType =
  | 'checking'
  | 'savings'
  | 'credit_card'
  | 'cash'
  | 'loan'
  | 'investment';

export type CategoryKind = 'income' | 'expense' | 'transfer';

export type RolloverMode = 'carry_positive' | 'carry_negative' | 'reset';

export type TransactionStatus = 'pending' | 'cleared' | 'reconciled';

export type BillCadence = 'monthly' | 'quarterly' | 'annual' | 'custom';

export type BillStatus = 'upcoming' | 'paid' | 'overdue' | 'skipped';

export type ProjectStatus = 'planned' | 'active' | 'done' | 'abandoned';

export interface Household {
  id: UUID;
  name: string;
  base_currency: string; // ISO 4217, default "CAD".
}

export interface User {
  id: UUID;
  household_id: UUID;
  email: string;
  role: Role;
  disabled_at: ISODateTime | null;
}

export interface Account {
  id: UUID;
  household_id: UUID;
  name: string;
  type: AccountType;
  institution: string;
  currency: string;
  starting_balance: DecimalString;
  closed_at: ISODateTime | null;
}

export interface Category {
  id: UUID;
  household_id: UUID;
  parent_id: UUID | null;
  name: string;
  kind: CategoryKind;
  is_budgetable: boolean;
  rollover_mode: RolloverMode;
}

export interface TransactionSplit {
  id: UUID;
  category_id: UUID | null;
  amount: DecimalString;
  memo: string;
}

export interface Transaction {
  id: UUID;
  account_id: UUID;
  date: ISODate;
  amount: DecimalString;
  original_currency: string;
  fx_rate: DecimalString | null;
  payee: string;
  memo: string;
  category_id: UUID | null;
  status: TransactionStatus;
  import_batch_id: UUID | null;
  splits: TransactionSplit[];
  receipt_attachment_id: UUID | null;
}

export interface BudgetAllocation {
  id: UUID;
  period_id: UUID;
  category_id: UUID;
  amount: DecimalString;
}

export interface BudgetPeriod {
  id: UUID;
  household_id: UUID;
  month: ISODate; // first-of-month.
  locked_at: ISODateTime | null;
}

export interface Bill {
  id: UUID;
  household_id: UUID;
  name: string;
  payee: string;
  amount: DecimalString | null; // null when variable.
  cadence: BillCadence;
  next_due: ISODate;
  account_id: UUID;
  autopay: boolean;
}

export interface BillInstance {
  id: UUID;
  bill_id: UUID;
  due_date: ISODate;
  amount_expected: DecimalString;
  paid_transaction_id: UUID | null;
  status: BillStatus;
}

export interface Project {
  id: UUID;
  household_id: UUID;
  name: string;
  status: ProjectStatus;
  budget: DecimalString | null;
  notes: string;
}

export interface ProjectTask {
  id: UUID;
  project_id: UUID;
  title: string;
  status: 'todo' | 'in_progress' | 'done';
  est_cost: DecimalString | null;
  actual_cost: DecimalString | null;
  due_date: ISODate | null;
  assignee_user_id: UUID | null;
}

export interface MaintenanceTask {
  id: UUID;
  household_id: UUID;
  title: string;
  cadence: string; // Free-form for now, e.g. "every 3 months".
  last_done: ISODate | null;
  next_due: ISODate;
  checklist: string[];
}

export interface Session {
  user: User;
  household: Household;
  // TOTP is mandatory (SPEC section 7.1). Once a session is fully established
  // this is true; intermediate "password-only" sessions should be rejected.
  totp_verified: boolean;
}
