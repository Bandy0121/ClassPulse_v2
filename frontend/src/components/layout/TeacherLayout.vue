<template>
  <div class="teacher-layout">
    <el-header class="header">
      <div class="header-left">
        <h2>ClassPulse · 教师端</h2>
      </div>
      <div class="header-right">
        <span v-if="auth.user" class="user-name">{{ auth.user.realName || auth.user.username }}</span>
        <el-dropdown trigger="click" @command="handleCommand">
          <el-avatar :icon="User" class="avatar-btn" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container class="body-wrap">
      <el-aside width="220px" class="sidebar">
        <el-menu :default-active="activeMenu" router>
          <el-menu-item index="/teacher">
            <el-icon><House /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/teacher/classes">
            <el-icon><Grid /></el-icon>
            <span>我的班级</span>
          </el-menu-item>
        </el-menu>
        <p class="menu-hint">测试与统计请在「班级详情」中进入对应班级操作。</p>
      </el-aside>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, House, Grid } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const activeMenu = computed(() => route.path)

async function handleCommand(cmd) {
  if (cmd === 'logout') {
    await auth.logout()
    ElMessage.success('已退出登录')
    await router.push({ name: 'teacher-login' })
  }
}
</script>

<style scoped>
.teacher-layout {
  min-height: 100vh;
  background-color: #f0f2f5;
}

.header {
  background-color: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
}

.header-left h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 14px;
  opacity: 0.95;
}

.avatar-btn {
  cursor: pointer;
}

.body-wrap {
  min-height: calc(100vh - 56px);
}

.sidebar {
  background-color: #fff;
  border-right: 1px solid #ebeef5;
}

.menu-hint {
  padding: 12px 16px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.main {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 56px);
  overflow-y: auto;
}
</style>
