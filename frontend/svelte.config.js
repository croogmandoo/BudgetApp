import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    // Node adapter — runs in the app container, listens on port 3000 in prod.
    adapter: adapter({
      out: 'build',
      precompress: false,
      envPrefix: ''
    }),
    alias: {
      $lib: 'src/lib'
    }
  }
};

export default config;
