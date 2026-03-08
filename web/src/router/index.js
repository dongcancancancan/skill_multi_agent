import Vue from 'vue'
import Router from 'vue-router'
import Login from '@/components/Login.vue'
import AiMain from '@/view/ai/aiMain.vue'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/list',
      name: 'list',
      component: () => import('@/view/manage/list.vue'),
    },
    {
      path: '/info',
      name: 'Info',
      component: () => import('@/view/manage/info.vue'),
    },
    {
      path: '/tool',
      name: 'Tool',
      component: () => import('@/view/manage/tool.vue'),
    },
    {
      path: '/',
      name: 'AiMain',
      component: AiMain,
      meta: { requiresAuth: true }
    },
    {
      path: '*',
      redirect: '/'
    }
  ]
})

// 路由守卫 - 检查认证
router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 检查token是否存在且未过期
    const token = localStorage.getItem('session_token')
    const expiresAt = localStorage.getItem('token_expires')
    
    if (!token || !expiresAt) {
      next('/login')
    } else {
      // 检查token是否过期
      const now = new Date()
      const expirationDate = new Date(expiresAt)
      
      if (now > expirationDate) {
        // token过期，清除存储并重定向到登录页
        localStorage.removeItem('session_token')
        localStorage.removeItem('token_expires')
        next('/login')
      } else {
        next()
      }
    }
  } else {
    next()
  }
})

export default router
