import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

fetch(API_BASE + '/')
  .then((res) => res.json())
  .then((data) => {
    if (data.project) {
      document.title = data.project
    }
  })
  .catch(() => {
    console.warn('无法获取项目名称，使用默认标题')
  })
  .finally(() => {
    createApp(App).mount('#app')
  })