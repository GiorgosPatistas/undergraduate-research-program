import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──────────────────────────────────────────────────────────────────
  const accessToken  = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user         = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const loading      = ref(false)
  const error        = ref(null)

  // ── Getters ────────────────────────────────────────────────────────────────
  const isLoggedIn = computed(() => !!accessToken.value)
  const isDoctor   = computed(() => user.value?.role === 'doctor')
  const isPatient  = computed(() => user.value?.role === 'patient')

  // ── Helpers ────────────────────────────────────────────────────────────────
  function setTokens(access, refresh) {
    accessToken.value  = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearAuth() {
    accessToken.value  = null
    refreshToken.value = null
    user.value         = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  // ── Actions ────────────────────────────────────────────────────────────────
  async function login(username, password) {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.post('/auth/login/', { username, password })
      setTokens(data.access, data.refresh)
      await fetchProfile()
      router.push({ name: 'services' })
    } catch (err) {
      error.value = err.response?.data?.detail || 'Invalid credentials.'
      throw err
    } finally {
      loading.value = false
    }
  }

  // register now accepts a full payload object
  async function register(payload) {
    loading.value = true
    error.value   = null
    try {
      await api.post('/auth/register/', payload)
      await login(payload.username, payload.password)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Registration failed.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    try {
      const { data } = await api.get('/auth/me/')
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
    } catch { /* non-critical */ }
  }

  async function refreshAccessToken() {
    try {
      const { data } = await api.post('/auth/refresh/', { refresh: refreshToken.value })
      accessToken.value = data.access
      localStorage.setItem('access_token', data.access)
      return data.access
    } catch {
      clearAuth()
      router.push({ name: 'login' })
      return null
    }
  }

  function logout() {
    clearAuth()
    router.push({ name: 'login' })
  }

  return {
    accessToken, user, loading, error,
    isLoggedIn, isDoctor, isPatient,
    login, register, logout, refreshAccessToken, fetchProfile
  }
})
