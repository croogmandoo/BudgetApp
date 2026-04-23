// See https://kit.svelte.dev/docs/types#app for reference.
// Populate these namespaces as the backend API surface solidifies.

declare global {
  namespace App {
    // interface Error {}
    interface Locals {
      // Populated by hooks.server.ts once auth is wired in.
      user?: {
        id: string;
        email: string;
        role: 'admin' | 'member' | 'viewer';
      } | null;
    }
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }

  interface ImportMetaEnv {
    readonly VITE_API_URL?: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

export {};
