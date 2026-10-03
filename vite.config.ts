import { defineConfig } from 'vite';

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? '/voxel-frontier/' : '/',
  build: { target: 'es2022' },
});
