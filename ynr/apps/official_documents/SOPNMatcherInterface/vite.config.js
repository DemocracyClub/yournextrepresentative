import {defineConfig} from 'vite'
import {svelte} from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [svelte()],
    optimizeDeps: {
        esbuildOptions: {
            target: 'esnext'
        }
    },
    build: {
        target: 'esnext',
        rollupOptions: {
            output: {
                entryFileNames: `assets/sopn-matcher-[name].js`,
                chunkFileNames: `assets/sopn-matcher-[name].js`,
                assetFileNames: `assets/sopn-matcher-[name].[ext]`
            }
        },
    }
})
