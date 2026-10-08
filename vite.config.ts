import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? '/voxel-frontier/' : '/',
  build: {
    target: 'es2022',
    rollupOptions: {
      input: {
        main: resolve(process.cwd(), 'index.html'),
        iea15: resolve(process.cwd(), 'iea15.html'),
        windTwin: resolve(process.cwd(), 'wind-twin.html'),
      },
    },
  },
});
