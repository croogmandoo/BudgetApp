import type { LayoutLoad } from './$types';
import { goto } from '$app/navigation';
import { browser } from '$app/environment';
import { api } from '$lib/api';
import { setSession, clearSession } from '$lib/stores/session';
import type { User, Household } from '$lib/types';

const PUBLIC_PATHS = ['/login', '/setup', '/totp-setup'];

export const load: LayoutLoad = async ({ url }) => {
  const isPublic = PUBLIC_PATHS.some((p) => url.pathname.startsWith(p));

  if (!browser) return {}; // SSR: skip (no cookies available in SvelteKit load)

  try {
    const data = await api.get<{ user: User; household: Household | null }>('/auth/me/');
    setSession({ user: data.user, household: data.household, totp_verified: true });
  } catch {
    clearSession();
    if (!isPublic) {
      await goto('/login');
    }
  }

  return {};
};
