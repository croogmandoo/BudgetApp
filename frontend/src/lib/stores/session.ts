/**
 * Current session store — stub.
 *
 * Holds the logged-in user + household for the SPA. Populated by a future
 * `+layout.server.ts` once the session-cookie auth path exists. Cleared on
 * logout. Using Svelte 5 runes via a small factory so the store is usable
 * from both `.svelte` and `.ts` modules.
 */

import { writable, type Writable } from 'svelte/store';
import type { Session } from '$lib/types';

export const session: Writable<Session | null> = writable(null);

export function setSession(next: Session | null): void {
  session.set(next);
}

export function clearSession(): void {
  session.set(null);
}
