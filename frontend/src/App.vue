<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import BookingHistoryPage from './pages/BookingHistoryPage.vue'
import LoginPage from './pages/LoginPage.vue'
import RegisterPage from './pages/RegisterPage.vue'
import SearchHistoryPage from './pages/SearchHistoryPage.vue'
import SearchPage from './pages/SearchPage.vue'
import { getCurrentAccount, getDemoUsers, logoutAccount } from './services/api.js'

const currentPath = ref(window.location.pathname)
const users = ref([])
const selectedUserId = ref('')
const startupError = ref('')
const authToken = ref(localStorage.getItem('expedia-mini-token') || '')
const authUser = ref(readStoredUser())
const isHistoryPage = computed(() => currentPath.value === '/bookings')
const isSearchHistoryPage = computed(() => currentPath.value === '/search-history')
const isLoginPage = computed(() => currentPath.value === '/login')
const isRegisterPage = computed(() => currentPath.value === '/register')

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('expedia-mini-user') || 'null')
  } catch {
    return null
  }
}

function navigate(path) {
  if (window.location.pathname !== path) window.history.pushState({}, '', path)
  currentPath.value = path
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handlePopState() {
  currentPath.value = window.location.pathname
}

async function loadUsers() {
  try {
    users.value = await getDemoUsers()
    selectedUserId.value = authUser.value?.user_id || users.value[0]?.user_id || ''
  } catch (error) {
    startupError.value = error.message || 'Demo travelers could not be loaded.'
  }
}

function handleAuthenticated(session) {
  authToken.value = session.token
  authUser.value = session.user
  localStorage.setItem('expedia-mini-token', session.token)
  localStorage.setItem('expedia-mini-user', JSON.stringify(session.user))
  if (!users.value.some((user) => user.user_id === session.user.user_id)) {
    users.value = [...users.value, session.user]
  }
  selectedUserId.value = session.user.user_id
  navigate('/')
}

async function handleLogout() {
  try {
    await logoutAccount(authToken.value)
  } catch {
    // The local session is still safe to clear if the short-lived token expired.
  }
  authToken.value = ''
  authUser.value = null
  localStorage.removeItem('expedia-mini-token')
  localStorage.removeItem('expedia-mini-user')
  selectedUserId.value = users.value[0]?.user_id || ''
  navigate('/')
}

async function validateStoredSession() {
  if (!authToken.value) return
  try {
    const session = await getCurrentAccount(authToken.value)
    authUser.value = session.user
  } catch {
    await handleLogout()
  }
}

onMounted(() => {
  window.addEventListener('popstate', handlePopState)
  loadUsers()
  validateStoredSession()
})
onBeforeUnmount(() => window.removeEventListener('popstate', handlePopState))
</script>

<template>
  <header class="site-header">
    <div class="page-container site-header-inner">
      <a class="brand-lockup" href="/" @click.prevent="navigate('/')">
        <span class="brand-mark" aria-hidden="true">E</span>
        <span>Expedia-Mini</span>
      </a>
      <nav class="site-nav" aria-label="Primary navigation">
        <a
          href="/"
          :aria-current="!isHistoryPage && !isSearchHistoryPage && !isLoginPage && !isRegisterPage ? 'page' : undefined"
          @click.prevent="navigate('/')"
        >
          Search stays
        </a>
        <a
          href="/bookings"
          :aria-current="isHistoryPage ? 'page' : undefined"
          @click.prevent="navigate('/bookings')"
        >
          Booking history
        </a>
        <a
          href="/search-history"
          :aria-current="isSearchHistoryPage ? 'page' : undefined"
          @click.prevent="navigate('/search-history')"
        >
          Search history
        </a>
        <template v-if="authUser">
          <span class="signed-in-user">{{ authUser.username }}</span>
          <button class="header-action" type="button" @click="handleLogout">Log out</button>
        </template>
        <template v-else>
          <a href="/login" @click.prevent="navigate('/login')">Sign in</a>
          <a class="header-action" href="/register" @click.prevent="navigate('/register')">
            Create account
          </a>
        </template>
      </nav>
    </div>
  </header>

  <div v-if="startupError" class="page-container global-error" role="alert">
    {{ startupError }} Check that the backend is running, then refresh the page.
  </div>

  <LoginPage
    v-if="isLoginPage"
    @authenticated="handleAuthenticated"
    @navigate="navigate"
  />
  <RegisterPage
    v-else-if="isRegisterPage"
    @authenticated="handleAuthenticated"
    @navigate="navigate"
  />
  <SearchHistoryPage
    v-else-if="isSearchHistoryPage"
    :auth-token="authToken"
    :auth-user="authUser"
    @navigate="navigate"
  />
  <BookingHistoryPage
    v-else-if="isHistoryPage"
    :users="users"
    :selected-user-id="selectedUserId"
    @update:selected-user-id="selectedUserId = $event"
    @navigate="navigate"
  />
  <SearchPage
    v-else
    :users="users"
    :selected-user-id="selectedUserId"
    :auth-token="authToken"
    @update:selected-user-id="selectedUserId = $event"
    @navigate="navigate"
  />
</template>
