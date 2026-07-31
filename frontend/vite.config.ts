import tailwindcss from '@tailwindcss/vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [vue(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modifyâfile watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      // Also always ignore data/db.json: the Express backend (server.ts) rewrites this
      // file on almost every request (create/start interview, submit answer, summary…).
      // Without this, Vite's default watcher treats each write as a source change and
      // triggers a full page reload — which is what caused pages like the report view
      // to reload in a loop right after fetching data.
      watch: process.env.DISABLE_HMR === 'true' ? null : { ignored: ['**/data/db.json'] },
    },
  };
});
