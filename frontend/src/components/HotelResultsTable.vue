<script setup>
defineProps({
  results: { type: Array, required: true },
  bookingTripId: { type: String, default: '' },
})

defineEmits(['book'])

const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
})

function formatUsd(value) {
  return usdFormatter.format(Number(value))
}

function formatDate(value) {
  return dateFormatter.format(new Date(`${value}T00:00:00Z`))
}
</script>

<template>
  <div class="result-card-grid" aria-label="Available hotel stays">
    <article v-for="stay in results" :key="stay.trip_id" class="result-card">
      <div class="result-card-main">
        <div class="result-location-row">
          <span class="result-location">{{ stay.city }}, {{ stay.state }}</span>
          <span class="stay-id">Stay {{ stay.trip_id }}</span>
        </div>
        <h3>{{ stay.hotel_name }}</h3>
        <p>{{ stay.trip_name }}</p>
        <p class="result-dates">
          {{ formatDate(stay.check_in) }} – {{ formatDate(stay.check_out) }}
          <span>· {{ stay.nights }} nights</span>
        </p>
      </div>
      <div class="result-price-action">
        <p><strong>{{ formatUsd(stay.estimated_stay_price_usd) }}</strong> estimated total</p>
        <span>{{ formatUsd(stay.nightly_rate_usd) }}/night</span>
        <button
          class="book-action"
          type="button"
          :disabled="Boolean(bookingTripId)"
          @click="$emit('book', stay)"
        >
          {{ bookingTripId === stay.trip_id ? 'Booking…' : 'Book this stay' }}
        </button>
      </div>
    </article>
  </div>
</template>
