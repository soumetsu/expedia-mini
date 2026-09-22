<script setup>
defineProps({
  results: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    required: true,
  },
  errorMessage: {
    type: String,
    required: true,
  },
})

const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
})

function formatUsd(value) {
  return usdFormatter.format(Number(value))
}

function formatDate(value) {
  return dateFormatter.format(new Date(`${value}T00:00:00`))
}
</script>

<template>
  <section class="recommendations" aria-labelledby="recommendations-title">
    <div class="section-heading">
      <div>
        <p class="eyebrow">A smart place to start</p>
        <h2 id="recommendations-title">Recommended stays</h2>
      </div>
      <p class="section-intro">
        Selected from the lowest estimated totals, with earlier dates used to break ties.
      </p>
    </div>

    <p v-if="loading" class="recommendation-message" role="status">
      Finding a few standout stays…
    </p>
    <p v-else-if="errorMessage" class="recommendation-message error-message" role="alert">
      {{ errorMessage }}
    </p>

    <div v-else class="recommendation-grid">
      <article
        v-for="(stay, index) in results"
        :key="stay.trip_id"
        class="recommendation-card"
      >
        <div class="recommendation-visual" :class="`recommendation-visual--${index + 1}`">
          <span class="recommendation-badge">{{ index === 0 ? 'Best value' : 'Great value' }}</span>
          <span class="city-mark" aria-hidden="true">{{ stay.city.charAt(0) }}</span>
          <p>{{ stay.city }}, {{ stay.state }}</p>
        </div>
        <div class="recommendation-body">
          <div>
            <h3>{{ stay.hotel_name }}</h3>
            <p class="trip-name">{{ stay.trip_name }}</p>
          </div>
          <dl class="stay-facts">
            <div>
              <dt>Dates</dt>
              <dd>{{ formatDate(stay.check_in) }} – {{ formatDate(stay.check_out) }}</dd>
            </div>
            <div>
              <dt>Stay</dt>
              <dd>{{ stay.nights }} {{ stay.nights === 1 ? 'night' : 'nights' }}</dd>
            </div>
          </dl>
          <div class="price-row">
            <p><strong>{{ formatUsd(stay.estimated_stay_price_usd) }}</strong> estimated total</p>
            <span>{{ formatUsd(stay.nightly_rate_usd) }}/night</span>
          </div>
        </div>
      </article>
    </div>

    <p class="recommendation-note">
      Recommendations use the current catalog only. Personalized suggestions based on recent
      searches are planned for a future update.
    </p>
  </section>
</template>
