<script setup>
import { onMounted, ref } from 'vue'

import { getSearchHistory } from '../services/api.js'

const props = defineProps({
  authToken: { type: String, default: '' },
  authUser: { type: Object, default: null },
})
const emit = defineEmits(['navigate'])
const history = ref([])
const loading = ref(false)
const errorMessage = ref('')

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
})

function formatDate(value) {
  return value ? dateFormatter.format(new Date(`${value}T00:00:00Z`)) : 'Any date'
}

async function loadHistory() {
  if (!props.authToken) return
  loading.value = true
  errorMessage.value = ''
  try {
    history.value = await getSearchHistory(props.authToken)
  } catch (error) {
    errorMessage.value = error.message || 'Search history could not be loaded.'
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<template>
  <main>
    <header class="subpage-hero">
      <div class="page-container subpage-hero-inner">
        <p class="eyebrow">Personal activity</p>
        <h1>Search history</h1>
        <p>Recent searches are private to your signed-in account.</p>
      </div>
    </header>
    <div class="page-container history-page">
      <section v-if="!authUser" class="empty-history" aria-labelledby="history-login-title">
        <span aria-hidden="true">⌁</span>
        <h2 id="history-login-title">Sign in to see your searches</h2>
        <p>Each account keeps a separate search history.</p>
        <button class="primary-action" type="button" @click="emit('navigate', '/login')">
          Sign in
        </button>
      </section>
      <section v-else class="search-history-card" aria-labelledby="search-history-title">
        <div class="section-heading">
          <div>
            <p class="eyebrow">{{ authUser.username }}</p>
            <h2 id="search-history-title">Your recent searches</h2>
          </div>
          <button class="secondary-action" type="button" @click="emit('navigate', '/')">
            Search stays
          </button>
        </div>
        <p v-if="loading" role="status">Loading your search history…</p>
        <p v-else-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
        <div v-else-if="history.length" class="history-list">
          <article v-for="item in history" :key="item.search_id" class="search-history-item">
            <div>
              <h3>{{ item.query }}</h3>
              <p>{{ formatDate(item.check_in) }} – {{ formatDate(item.check_out) }}</p>
            </div>
            <span class="history-count">{{ item.result_count }} stays</span>
          </article>
        </div>
        <div v-else class="empty-history empty-history--compact">
          <h2>No searches yet</h2>
          <p>Your searches will appear here after you sign in.</p>
        </div>
      </section>
    </div>
  </main>
</template>
