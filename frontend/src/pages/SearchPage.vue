<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

import HotelMap from '../components/HotelMap.vue'
import HotelSearchForm from '../components/HotelSearchForm.vue'
import NearbyHotelList from '../components/NearbyHotelList.vue'
import RecommendedStays from '../components/RecommendedStays.vue'
import {
  createBooking,
  getRecommendedHotels,
  searchNearbyHotels,
} from '../services/api.js'

const props = defineProps({
  users: { type: Array, required: true },
  selectedUserId: { type: String, required: true },
  authToken: { type: String, default: '' },
})
const emit = defineEmits(['update:selectedUserId', 'navigate'])

const postcode = ref('')
const searchedPostcode = ref('')
const loading = ref(false)
const results = ref([])
const resultCount = ref(0)
const searchCenter = ref(null)
const searchScope = ref('')
const searchRadiusMiles = ref(null)
const hotelSource = ref('')
const postcodeSource = ref('')
const hasSearched = ref(false)
const errorMessage = ref('')
const selectedPlaceId = ref('')
const recommendations = ref([])
const recommendationsLoading = ref(true)
const recommendationsError = ref('')
const bookingTripId = ref('')
const bookingMessage = ref('')
const bookingError = ref('')

const noResults = computed(
  () => hasSearched.value && !loading.value && !errorMessage.value && resultCount.value === 0,
)
const expandedSearch = computed(() => searchScope.value === 'expanded radius')

const resolvedLocation = computed(() => {
  if (!searchCenter.value) return ''
  return [searchCenter.value.locality, searchCenter.value.state].filter(Boolean).join(', ')
})

async function handleSearch({ postcode: requestedPostcode }) {
  postcode.value = requestedPostcode
  searchedPostcode.value = requestedPostcode
  loading.value = true
  hasSearched.value = false
  errorMessage.value = ''
  results.value = []
  resultCount.value = 0
  searchCenter.value = null
  searchScope.value = ''
  searchRadiusMiles.value = null
  hotelSource.value = ''
  postcodeSource.value = ''
  selectedPlaceId.value = ''

  try {
    const response = await searchNearbyHotels(requestedPostcode, props.authToken)
    results.value = response.results
    resultCount.value = response.count
    searchCenter.value = response.center
    searchScope.value = response.search_scope
    searchRadiusMiles.value = response.search_radius_miles
    hotelSource.value = response.hotel_source
    postcodeSource.value = response.postcode_source
    selectedPlaceId.value = response.results[0]?.place_id || ''
    hasSearched.value = true
  } catch (error) {
    hasSearched.value = true
    errorMessage.value = error.message || 'The live hotel search could not be completed.'
  } finally {
    loading.value = false
  }
}

function handleClear() {
  searchedPostcode.value = ''
  results.value = []
  resultCount.value = 0
  searchCenter.value = null
  searchScope.value = ''
  searchRadiusMiles.value = null
  hotelSource.value = ''
  postcodeSource.value = ''
  hasSearched.value = false
  errorMessage.value = ''
  selectedPlaceId.value = ''
}

function selectHotel(placeId) {
  selectedPlaceId.value = placeId
}

async function selectHotelFromMap(placeId) {
  selectedPlaceId.value = placeId
  const index = results.value.findIndex((hotel) => hotel.place_id === placeId)
  if (index < 0) return
  await nextTick()
  const card = document.getElementById(`nearby-hotel-${index}`)
  card?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  card?.focus({ preventScroll: true })
}

async function handleBook(stay) {
  if (!props.selectedUserId) {
    bookingError.value = 'Choose a demo traveler before creating a simulated booking.'
    return
  }
  bookingTripId.value = stay.trip_id
  bookingMessage.value = ''
  bookingError.value = ''

  try {
    const booking = await createBooking(props.selectedUserId, stay.trip_id)
    bookingMessage.value = `Demo booking ${booking.booking_id} was created for ${booking.display_name}.`
  } catch (error) {
    bookingError.value = error.message || 'This simulated booking could not be created.'
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
    recommendationsError.value = 'The fictional booking catalog is temporarily unavailable.'
  } finally {
    recommendationsLoading.value = false
  }
}

onMounted(loadRecommendations)
</script>

<template>
  <main>
    <header class="hero hero--live-search">
      <div class="page-container hero-inner">
        <div class="hero-copy">
          <p class="eyebrow">Live place discovery</p>
          <h1>Explore hotels inside or near a ZIP code.</h1>
          <p>
            Search a five-digit U.S. ZIP code to compare live Geoapify hotel places in a
            connected list and interactive map. If its boundary is empty, the search expands
            to the nearest populated radius.
          </p>
          <ul class="hero-points" aria-label="Live search details">
            <li>ZIP boundary first</li>
            <li>Live 5, 15, or 30 mile fallback</li>
            <li>Connected list and map</li>
            <li>Distance from ZIP center</li>
          </ul>
        </div>
      </div>
    </header>

    <div class="page-container content-stack">
      <section class="search-panel live-search-panel" aria-labelledby="search-title">
        <div class="search-panel-heading live-search-heading">
          <p class="eyebrow">Search live hotel places</p>
          <h2 id="search-title">Which ZIP code should we explore?</h2>
        </div>
        <HotelSearchForm
          v-model="postcode"
          :loading="loading"
          @clear="handleClear"
          @search="handleSearch"
        />
      </section>

      <section
        v-if="hasSearched || loading"
        class="search-results live-search-results"
        aria-labelledby="search-results-title"
      >
        <div class="section-heading section-heading--results">
          <div>
            <p class="eyebrow">Live provider results</p>
            <h2 id="search-results-title">
              {{ expandedSearch ? 'Hotels near' : 'Hotels inside' }} ZIP {{ searchedPostcode }}
            </h2>
          </div>
          <p v-if="resolvedLocation" class="section-intro">
            ZIP center resolved near {{ resolvedLocation }}. Distances below are straight-line
            estimates from that reference point.
          </p>
        </div>

        <ul v-if="searchCenter" class="live-source-list" aria-label="Live search data sources">
          <li><strong>Hotel records:</strong> {{ hotelSource }} (live)</li>
          <li><strong>ZIP center:</strong> {{ postcodeSource }}</li>
          <li><strong>Map imagery:</strong> OpenStreetMap</li>
        </ul>

        <div class="search-status live-search-status" aria-live="polite" aria-atomic="true">
          <p v-if="loading" role="status">
            Resolving the ZIP code and searching live Geoapify hotel records…
          </p>
          <p v-else-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
          <p v-else-if="noResults && expandedSearch" role="status">
            ZIP {{ searchedPostcode }} resolved successfully, but Geoapify returned no hotels
            inside its boundary or within {{ searchRadiusMiles }} miles of its center.
          </p>
          <p v-else-if="noResults" role="status">
            ZIP {{ searchedPostcode }} resolved successfully, but Geoapify returned no hotels.
          </p>
          <p v-else-if="expandedSearch" class="result-count" role="status">
            No exact-boundary hotels were available. {{ resultCount }}
            {{ resultCount === 1 ? 'hotel was' : 'hotels were' }} found in the first populated
            Geoapify radius: within {{ searchRadiusMiles }} miles of ZIP {{ searchedPostcode }}'s
            center. Results outside the ZIP are labeled below.
          </p>
          <p v-else class="result-count" role="status">
            {{ resultCount }} {{ resultCount === 1 ? 'hotel' : 'hotels' }} found inside ZIP
            {{ searchedPostcode }}. Select a card or marker to match it in both views.
          </p>
        </div>

        <div v-if="results.length && searchCenter" class="live-results-layout">
          <div class="live-results-list-panel">
            <NearbyHotelList
              :results="results"
              :postcode="searchedPostcode"
              :show-postcode-relation="expandedSearch"
              :selected-place-id="selectedPlaceId"
              @select="selectHotel"
            />
          </div>
          <HotelMap
            :results="results"
            :center="searchCenter"
            :selected-place-id="selectedPlaceId"
            @select="selectHotelFromMap"
          />
        </div>

        <p v-if="results.length" class="provider-note">
          Hotel records are pulled live from Geoapify Places through FastAPI—not from the local
          CSV or SQLite demo catalog. Names, addresses, postcodes, and coordinates are shown only
          when supplied by Geoapify. No price, rating, room availability, or booking claim is
          inferred.
        </p>
      </section>

      <section class="demo-booking-toolbar" aria-labelledby="demo-booking-title">
        <div>
          <p class="eyebrow">Simulation controls</p>
          <h2 id="demo-booking-title">Keep the booking exercise separate</h2>
          <p>
            Choose a fictional traveler for the classroom catalog below. This does not affect the
            live Geoapify search.
          </p>
        </div>
        <div class="traveler-select">
          <label for="demo-traveler">Demo traveler</label>
          <select
            id="demo-traveler"
            :value="selectedUserId"
            :disabled="!users.length"
            @change="emit('update:selectedUserId', $event.target.value)"
          >
            <option v-for="user in users" :key="user.user_id" :value="user.user_id">
              {{ user.display_name }}
            </option>
          </select>
        </div>
      </section>

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

      <RecommendedStays
        :results="recommendations"
        :loading="recommendationsLoading"
        :error-message="recommendationsError"
        :booking-trip-id="bookingTripId"
        @book="handleBook"
      />

      <footer class="page-footer">
        <p>
          Live hotel places come from Geoapify. The booking sandbox uses separate fictional
          classroom data.
        </p>
      </footer>
    </div>
  </main>
</template>
