import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const token = ref(localStorage.getItem('fg_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('fg_user') || '{}'))
  const loading = ref(false)
  const error = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '用户')

  function login(authToken, userInfo) {
    token.value = authToken
    user.value = userInfo
    localStorage.setItem('fg_token', authToken)
    localStorage.setItem('fg_user', JSON.stringify(userInfo))
  }

  function logout() {
    token.value = ''
    user.value = {}
    loading.value = false
    error.value = null
    localStorage.removeItem('fg_token')
    localStorage.removeItem('fg_user')
  }

  function setLoading(val) {
    loading.value = val
  }

  function setError(msg) {
    error.value = msg
  }

  return {
    token, user, loading, error,
    isLoggedIn, username,
    login, logout, setLoading, setError,
  }
})
