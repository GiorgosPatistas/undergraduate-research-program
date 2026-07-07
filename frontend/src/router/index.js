import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/features/account/store'

import HomeView from '@/features/home/views/HomeView.vue'
import LoginView from '@/features/account/views/LoginView.vue'
import RegisterView from '@/features/account/views/RegisterView.vue'
import ServicesView from '@/features/predictions/views/ServicesView.vue'
import BlogView from '@/features/blog/views/BlogView.vue'
import ProfileView from '@/features/account/views/ProfileView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: 'Smart Healthcare — Home' }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { title: 'Login', guestOnly: true }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { title: 'Register', guestOnly: true }
  },
  {
    path: '/services',
    name: 'services',
    component: ServicesView,
    meta: { title: 'Services', requiresAuth: true }
  },
  {
    path: '/blog',
    name: 'blog',
    component: BlogView,
    meta: { title: 'Blog', requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: { title: 'My Profile', requiresAuth: true }
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0, behavior: 'smooth' }
  }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Smart Healthcare'
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }
  if (to.meta.guestOnly && auth.isLoggedIn) {
    return next({ name: 'services' })
  }
  next()
})

export default router
