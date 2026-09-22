<script setup>
import { computed, onMounted, ref } from 'vue'

import HotelResultsTable from '../components/HotelResultsTable.vue'
import HotelSearchForm from '../components/HotelSearchForm.vue'
import RecommendedStays from '../components/RecommendedStays.vue'
import { createBooking, getRecommendedHotels, searchHotels } from '../services/api.js'

const props = defineProps({
  users: { type: Array, required: true },
  selectedUserId: { type: String, required: true },
  authToken: { type: String, default: '' },
})
const emit = defineEmits(['update:selectedUserId', 'navigate'])

const query = ref('')
const checkIn = ref('')
const checkOut = ref('')
const loading = ref(false)
const results = ref([])
const resultCount = ref(0)
const hasSearched = ref(false)
const errorMessage = ref('')
const recommendations = ref([])
const recommendationsLoading = ref(true)
const recommendationsError = ref('')
const bookingTripId = ref('')
const bookingMessage = ref('')
const bookingError = ref('')

const noResults = computed(
  () => hasSearched.value && !loading.value && !errorMessage.value && resultCount.value === 0,
)

async function handleSearch(criteria) {
  query.value = criteria.location
  loading.value = true
  hasSearched.value = false
  errorMessage.value = ''
  bookingMessage.value = ''
  bookingError.value = ''
  results.value = []
  resultCount.value = 0

  try {
    const response = await searchHotels(criteria.location, criteria, props.authToken)
    results.value = response.results
    resultCount.value = response.count
    hasSearched.value = true
  } catch (error) {
    hasSearched.value = true
    errorMessage.value = error.message || 'The location search could not be completed.'
  } finally {
    loading.value = false
  }
}

function handleClear() {
  results.value = []
  resultCount.value = 0
  hasSearched.value = false
  errorMessage.value = ''
  bookingMessage.value = ''
  bookingError.value = ''
  bookingTripId.value = ''
}

async function handleBook(stay) {
  bookingTripId.value = stay.trip_id
  bookingMessage.value = ''
  bookingError.value = ''

  try {
    const booking = await createBooking(props.selectedUserId, stay.trip_id)
    bookingMessage.value = `${booking.hotel_name} is booked for ${booking.display_name}.`
  } catch (error) {
    bookingError.value = error.message || 'This stay could not be booked.'
  } finally {
    bookingTripId.value = ''
  }
}

async function loadRecommendations() {
  recommendationsLoading.value = true
  recommendationsError.value = ''
  try {
    const response = await getRecommendedHotels()
    recommendations.value = response.results
  } catch {
    recommendationsError.value = 'Recommended stays are temporarily unavailable.'
  } finally {
    recommendationsLoading.value = false
  }
}

onMounted(loadRecommendations)
</script>

<template>
  <main>
    <header class="hero">
      <div class="page-container hero-inner">
        <div class="hero-copy">
          <p class="eyebrow">Curated city stays</p>
          <h1>Find a stay that fits your trip.</h1>
          <p>
            Search available hotel stays by destination, add optional travel dates, and create a
            simulated booking in one clear view.
          </p>
          <ul class="hero-points" aria-label="Search benefits">
            <li>Fixed-date stays</li>
            <li>Clear price estimates</li>
            <li>Simple booking history</li>
          </ul>
        </div>
      </div>
    </header>

    <div class="page-container content-stack">
      <section class="search-panel" aria-labelledby="search-title">
        <div class="search-panel-heading">
          <p class="eyebrow">Start your search</p>
          <h2 id="search-title">Where are you heading?</h2>
        </div>
        <HotelSearchForm
          v-model="query"
          v-model:check-in="checkIn"
          v-model:check-out="checkOut"
          :users="users"
          :selected-user-id="selectedUserId"
          :loading="loading"
          @update:selected-user-id="emit('update:selectedUserId', $event)"
          @clear="handleClear"
          @search="handleSearch"
        />
      </section>

      <section
        v-if="hasSearched || loading"
        class="search-results"
        aria-labelledby="search-results-title"
      >
        <div class="section-heading section-heading--results">
          <div>
            <p class="eyebrow">Your search</p>
            <h2 id="search-results-title">Available stays</h2>
          </div>
        </div>

        <div class="search-status" aria-live="polite" aria-atomic="true">
          <p v-if="loading" role="status">Searching available stays…</p>
          <p v-else-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
          <p v-else-if="noResults" role="status">
            No stays matched “{{ query }}”. Try another city, state, or hotel name.
          </p>
          <p v-else class="result-count" role="status">
            {{ resultCount }} {{ resultCount === 1 ? 'stay' : 'stays' }} found for “{{ query }}”.
          </p>
        </div>

        <div v-if="bookingMessage || bookingError" class="booking-feedback" aria-live="polite">
          <p v-if="bookingMessage" class="success-message">{{ bookingMessage }}</p>
          <p v-if="bookingError" class="error-message" role="alert">{{ bookingError }}</p>
          <button
            v-if="bookingMessage"
            class="text-action"
            type="button"
            @click="emit('navigate', '/bookings')"
          >
            View booking history →
          </button>
        </div>

        <HotelResultsTable
          v-if="results.length"
          :results="results"
          :booking-trip-id="bookingTripId"
          @book="handleBook"
        />
      </section>

      <RecommendedStays
        :results="recommendations"
        :loading="recommendationsLoading"
        :error-message="recommendationsError"
      />

      <footer class="page-footer">
        <p>Fictional stays, bookings, and estimated prices for demonstration.</p>
      </footer>
    </div>
  </main>
</template>
