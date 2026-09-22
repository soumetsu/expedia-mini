<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import BookingHistoryPage from './pages/BookingHistoryPage.vue'
import SearchPage from './pages/SearchPage.vue'
import { getDemoUsers } from './services/api.js'

const currentPath = ref(window.location.pathname)
const users = ref([])
const selectedUserId = ref('')
const startupError = ref('')
const isHistoryPage = computed(() => currentPath.value === '/bookings')

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
    selectedUserId.value = users.value[0]?.user_id || ''
  } catch (error) {
    startupError.value = error.message || 'Demo travelers could not be loaded.'
  }
}

onMounted(() => {
  window.addEventListener('popstate', handlePopState)
  loadUsers()
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
        <a href="/" :aria-current="!isHistoryPage ? 'page' : undefined" @click.prevent="navigate('/')">
          Search stays
        </a>
        <a
          href="/bookings"
          :aria-current="isHistoryPage ? 'page' : undefined"
          @click.prevent="navigate('/bookings')"
        >
          Booking history
        </a>
      </nav>
    </div>
  </header>

  <div v-if="startupError" class="page-container global-error" role="alert">
    {{ startupError }} Check that the backend is running, then refresh the page.
  </div>

  <BookingHistoryPage
    v-if="isHistoryPage"
    :users="users"
    :selected-user-id="selectedUserId"
    @update:selected-user-id="selectedUserId = $event"
    @navigate="navigate"
  />
  <SearchPage
    v-else
    :users="users"
    :selected-user-id="selectedUserId"
    @update:selected-user-id="selectedUserId = $event"
    @navigate="navigate"
  />
</template>
