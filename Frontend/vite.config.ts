import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('/echarts/') || id.includes('zrender')) return 'echarts'
            if (id.includes('/vue/') || id.includes('/@vue/')) return 'vue-vendor'
            return 'vendor'
          }
        },
      },
    },
  },
})