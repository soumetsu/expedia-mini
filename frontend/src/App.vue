<script setup>
import { computed, ref } from 'vue'

import HotelResultsTable from './components/HotelResultsTable.vue'
import HotelSearchForm from './components/HotelSearchForm.vue'
import { searchHotels } from './services/api.js'

const query = ref('')
const loading = ref(false)
const results = ref([])
const resultCount = ref(0)
const hasSearched = ref(false)
const errorMessage = ref('')

const noResults = computed(
  () => hasSearched.value && !loading.value && !errorMessage.value && resultCount.value === 0,
)

async function handleSearch(normalizedQuery) {
  query.value = normalizedQuery
  loading.value = true
  hasSearched.value = false
  errorMessage.value = ''
  results.value = []
  resultCount.value = 0

  try {
    const response = await searchHotels(normalizedQuery)
    results.value = response.results
    resultCount.value = response.count
    hasSearched.value = true
  } catch {
    hasSearched.value = true
    errorMessage.value =
      'The hotel search could not be completed. Check that the backend is running and try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="page-container">
    <header class="page-header">
      <h1>Expedia-Mini</h1>
      <p>Search the available hotel stays by entering all or part of a hotel name.</p>
    </header>

    <HotelSearchForm v-model="query" :loading="loading" @search="handleSearch" />

    <div class="search-status" aria-live="polite" aria-atomic="true">
      <p v-if="loading" role="status">Searching for available stays…</p>
      <p v-else-if="errorMessage" class="error-message" role="alert">
        {{ errorMessage }}
      </p>
      <p v-else-if="noResults" role="status">
        No hotels matched “{{ query }}”. Try another hotel name.
      </p>
      <p v-else-if="hasSearched" class="result-count" role="status">
        {{ resultCount }} {{ resultCount === 1 ? 'stay' : 'stays' }} found for “{{ query }}”.
      </p>
    </div>

    <HotelResultsTable v-if="results.length" :results="results" />
  </main>
</template>
