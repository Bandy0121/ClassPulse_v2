/**
 * 主入口文件
 *
 * 本文件是 Vue 应用的入口点，负责：
 * 1. 创建 Vue 应用实例
 * 2. 全局插件和组件注册
 * 3. 挂载应用到 DOM
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

// 创建 Vue 应用实例
const app = createApp(App)

// 使用 Pinia 状态管理
// Pinia 是 Vue 3 的官方状态管理库，用于管理应用的全局状态
const pinia = createPinia()

// 注册全局插件
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 注册全局图标组件
// ElementPlusIconsVue 包含所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 挂载应用到 DOM
// 将 Vue 应用挂载到 index.html 中的 #app 元素
app.mount('#app')

// 全局错误处理
// 捕获并处理应用中的未 caught 错误
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err, info)
}
