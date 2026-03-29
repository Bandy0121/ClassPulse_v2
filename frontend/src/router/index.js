/**
 * 路由配置文件
 *
 * 本文件定义了应用的所有路由，包括：
 * 1. 公共路由（登录、注册）
 * 2. 教师端路由
 * 3. 学生端路由
 *
 * 路由守卫用于保护需要认证的页面
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 登录页面组件
const TeacherLogin = () => import('@/views/auth/TeacherLogin.vue')
const StudentLogin = () => import('@/views/auth/StudentLogin.vue')
const TeacherRegister = () => import('@/views/auth/TeacherRegister.vue')
const StudentRegister = () => import('@/views/auth/StudentRegister.vue')

// 必须先定义布局组件（避免循环引用）
const TeacherLayout = () => import('@/components/layout/TeacherLayout.vue')
const StudentLayout = () => import('@/components/layout/StudentLayout.vue')

// 教师端页面组件
const TeacherDashboard = () => import('@/views/teacher/Dashboard.vue')
const ClassList = () => import('@/views/teacher/ClassList.vue')
const ClassDetail = () => import('@/views/teacher/ClassDetail.vue')
const AssessmentCreate = () => import('@/views/teacher/AssessmentCreate.vue')
const AssessmentList = () => import('@/views/teacher/AssessmentList.vue')
const Statistics = () => import('@/views/teacher/Statistics.vue')
const ClassStatistics = () => import('@/views/teacher/ClassStatistics.vue')
const CheckinRecords = () => import('@/views/teacher/CheckinRecords.vue')

// 学生端页面组件
const StudentDashboard = () => import('@/views/student/Dashboard.vue')
const StudentClassList = () => import('@/views/student/ClassList.vue')
const StudentAssessments = () => import('@/views/student/StudentAssessments.vue')
const AssessmentTaking = () => import('@/views/student/AssessmentTaking.vue')
const AssessmentResult = () => import('@/views/student/AssessmentResult.vue')
const History = () => import('@/views/student/History.vue')
const StudentCheckin = () => import('@/views/student/Checkin.vue')

// 创建路由实例
const router = createRouter({
  // 使用 HTML5 History 模式
  history: createWebHistory(import.meta.env.BASE_URL),

  // 路由配置
  routes: [
    // ==================== 公共路由 ====================
    {
      path: '/',
      redirect: '/teacher/login'
    },

    // 通用登录路径（重定向到教师登录）
    {
      path: '/login',
      redirect: '/teacher/login'
    },

    // 教师登录
    {
      path: '/teacher/login',
      name: 'teacher-login',
      component: TeacherLogin
    },

    // 学生登录
    {
      path: '/student/login',
      name: 'student-login',
      component: StudentLogin
    },

    // 教师注册
    {
      path: '/teacher/register',
      name: 'teacher-register',
      component: TeacherRegister
    },

    // 学生注册
    {
      path: '/student/register',
      name: 'student-register',
      component: StudentRegister
    },

    // ==================== 教师端路由 ====================
    {
      path: '/teacher',
      component: TeacherLayout,
      meta: { role: 'teacher', requiresAuth: true },
      children: [
        // 教师仪表盘
        {
          path: '',
          name: 'teacher-dashboard',
          component: TeacherDashboard
        },

        // 班级相关路由
        {
          path: 'classes',
          name: 'teacher-classes',
          component: ClassList
        },
        {
          path: 'classes/:id/statistics',
          name: 'teacher-class-statistics',
          component: ClassStatistics,
          props: true
        },
        {
          path: 'classes/:id',
          name: 'teacher-class-detail',
          component: ClassDetail,
          props: true
        },

        // 测试相关路由
        {
          path: 'classes/:id/assessments/create',
          name: 'teacher-assessment-create',
          component: AssessmentCreate,
          props: true
        },
        {
          path: 'classes/:id/assessments',
          name: 'teacher-assessment-list',
          component: AssessmentList,
          props: true
        },
        {
          path: 'assessments/:id/statistics',
          name: 'teacher-statistics',
          component: Statistics,
          props: true
        },

        // 签到相关路由
        {
          path: 'classes/:id/checkins',
          name: 'teacher-checkins',
          component: CheckinRecords,
          props: true
        }
      ]
    },

    // ==================== 学生端路由 ====================
    {
      path: '/student',
      component: StudentLayout,
      meta: { role: 'student', requiresAuth: true },
      children: [
        // 学生仪表盘
        {
          path: '',
          name: 'student-dashboard',
          component: StudentDashboard
        },

        // 班级相关路由
        {
          path: 'classes',
          name: 'student-classes',
          component: StudentClassList
        },

        {
          path: 'assessments',
          name: 'student-assessments',
          component: StudentAssessments
        },
        {
          path: 'assessments/:id/take',
          name: 'student-assessment-take',
          component: AssessmentTaking,
          props: true
        },
        {
          path: 'assessments/:id/result',
          name: 'student-assessment-result',
          component: AssessmentResult,
          props: true
        },
        {
          path: 'checkin',
          name: 'student-checkin',
          component: StudentCheckin
        },
        {
          path: 'history',
          name: 'student-history',
          component: History
        }
      ]
    },

    // 404 页面
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/common/NotFound.vue')
    }
  ]
})

// ==================== 路由守卫 ====================

/**
 * 路由守卫 - 在导航前执行
 */
router.beforeEach((to, from, next) => {
  const publicNames = new Set([
    'teacher-login',
    'student-login',
    'teacher-register',
    'student-register',
    'not-found'
  ])

  if (publicNames.has(to.name)) {
    next()
    return
  }

  const store = useAuthStore()

  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!store.isLoggedIn) {
      next({
        name: to.meta.role === 'teacher' ? 'teacher-login' : 'student-login',
        query: { redirect: to.fullPath }
      })
      return
    }
    if (store.user && store.user.userType !== to.meta.role) {
      next({
        name: store.user.userType === 'teacher' ? 'teacher-dashboard' : 'student-dashboard'
      })
      return
    }
  }

  next()
})

/**
 * 路由守卫 - 导航后执行
 *
 * 用途：
 * 1. 修改页面标题
 * 2. 页面统计
 */
router.afterEach((to) => {
  // 设置页面标题
  const pageTitle = getPageRouteTitle(to.name)
  document.title = pageTitle ? `${pageTitle} - ClassPulse` : 'ClassPulse - 学生课堂测试反馈系统'
})

/**
 * 获取路由的页面标题
 */
function getPageRouteTitle(routeName) {
  const titles = {
    'teacher-login': '教师登录',
    'student-login': '学生登录',
    'teacher-register': '教师注册',
    'student-register': '学生注册',
    'teacher-dashboard': '教师仪表盘',
    'teacher-classes': '我的班级',
    'teacher-class-detail': '班级详情',
    'teacher-class-statistics': '班级统计',
    'teacher-assessment-create': '创建测试',
    'teacher-assessment-list': '测试列表',
    'teacher-statistics': '测试统计',
    'teacher-checkins': '签到记录',
    'student-dashboard': '学生仪表盘',
    'student-classes': '我的班级',
    'student-assessments': '随堂测试',
    'student-assessment-take': '答题',
    'student-assessment-result': '测试结果',
    'student-checkin': '课堂签到',
    'student-history': '测试历史'
  }

  return titles[routeName] || ''
}

export default router
