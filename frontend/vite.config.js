/**
 * Vite 配置文件
 *
 * 本文件用于配置 Vite 构建工具的行为
 */

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  // 插件配置
  plugins: [vue()],

  // 项目根目录
  root: path.resolve(__dirname, '.'),

  // 开发服务器配置
  server: {
    port: 5173,              // 开发服务器端口
    strictPort: true,        // 端口被占用时直接报错，不自动切换
    host: '0.0.0.0',         // 监听所有网络接口
    proxy: {
      // 代理 API 请求到后端
      '/api': {
        target: 'http://localhost:5000',  // 后端服务器地址
        changeOrigin: true,               // 更改请求源
        secure: false                     // 不验证 HTTPS 证书
      }
    }
  },

  // 构建配置
  build: {
    outDir: 'dist',
    sourcemap: false
  },

  // Resolve 配置
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')  // 设置 @ 别名指向 src 目录
    }
  },

  // CSS 配置
  css: {
    postcss: path.join(__dirname, 'postcss.config.js')
  }
})
