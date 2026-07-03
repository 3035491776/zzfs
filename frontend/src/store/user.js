import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const unreadCount = ref(0)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')
  const userName = computed(() => user.value?.real_name || '用户')
  const userRole = computed(() => user.value?.role || '')

  // Actions
  async function login(username, password) {
    const res = await authApi.login({ username, password })
    token.value = res.data.token
    user.value = res.data.user

    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))

    return res.data
  }

  async function register(form) {
    const res = await authApi.register(form)
    return res.data
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (e) {
      // ignore
    }
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchUserInfo() {
    const res = await authApi.getMe()
    user.value = res.data.user
    localStorage.setItem('user', JSON.stringify(res.data.user))
  }

  async function fetchUnreadCount() {
    try {
      const res = await authApi.getNotificationsUnread()
      unreadCount.value = res.data.count
    } catch (e) {
      // ignore
    }
  }

  return {
    token, user, unreadCount,
    isLoggedIn, isAdmin, isTeacher, isStudent, userName, userRole,
    login, register, logout, fetchUserInfo, fetchUnreadCount,
  }
})
