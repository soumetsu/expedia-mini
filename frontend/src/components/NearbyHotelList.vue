<script setup>
const props = defineProps({
  results: { type: Array, required: true },
  postcode: { type: String, required: true },
  showPostcodeRelation: { type: Boolean, default: false },
  selectedPlaceId: { type: String, default: '' },
})

defineEmits(['select'])

function formatDistance(distanceMiles) {
  if (distanceMiles < 0.05) return 'Less than 0.1 mi'
  return `${distanceMiles.toFixed(1)} mi`
}

function distanceBand(distanceMiles) {
  if (distanceMiles > 15) {
    return { label: 'Very far', className: 'hotel-card-distance--very-far' }
  }
  if (distanceMiles > 5) {
    return { label: 'Far', className: 'hotel-card-distance--far' }
  }
  return { label: 'Nearby', className: 'hotel-card-distance--near' }
}

function postcodeRelation(hotel) {
  if (hotel.inside_searched_postcode === true) {
    return `Inside ZIP ${props.postcode}`
  }
  if (hotel.inside_searched_postcode === false) {
    return hotel.postcode
      ? `Outside ZIP ${props.postcode} · provider postcode ${hotel.postcode}`
      : `Outside ZIP ${props.postcode}`
  }
  return 'Provider postcode unavailable'
}

function googleMapsUrl(hotel) {
  const query = hotel.formatted_address || `${hotel.latitude},${hotel.longitude}`
  const parameters = new URLSearchParams({ api: '1', query })
  return `https://www.google.com/maps/search/?${parameters.toString()}`
}

function googleMapsLabel(hotel) {
  return hotel.formatted_address
    ? 'Open address in Google Maps'
    : 'Open coordinates in Google Maps'
}
</script>

<template>
  <ol class="nearby-hotel-list" aria-label="Live hotels inside or near the searched ZIP">
    <li v-for="(hotel, index) in results" :key="hotel.place_id">
      <article
        class="nearby-hotel-card"
        :class="{ 'nearby-hotel-card--selected': selectedPlaceId === hotel.place_id }"
      >
        <button
          :id="`nearby-hotel-${index}`"
          class="nearby-hotel-select"
          type="button"
          :aria-pressed="selectedPlaceId === hotel.place_id"
          @click="$emit('select', hotel.place_id)"
        >
          <span class="hotel-result-number" aria-hidden="true">{{ index + 1 }}</span>
          <span class="hotel-card-copy">
            <span class="hotel-card-heading">{{ hotel.name || 'Name unavailable' }}</span>
            <span v-if="hotel.formatted_address" class="hotel-card-address">
              {{ hotel.formatted_address }}
            </span>
            <span v-else class="hotel-card-address hotel-card-address--missing">
              Address unavailable
            </span>
            <span
              v-if="showPostcodeRelation"
              class="hotel-card-postcode-relation"
              :class="{
                'hotel-card-postcode-relation--outside': hotel.inside_searched_postcode === false,
                'hotel-card-postcode-relation--unknown': hotel.inside_searched_postcode == null,
              }"
            >
              {{ postcodeRelation(hotel) }}
            </span>
            <span
              class="hotel-card-distance"
              :class="distanceBand(hotel.distance_miles).className"
            >
              {{ distanceBand(hotel.distance_miles).label }} ·
              {{ formatDistance(hotel.distance_miles) }} from ZIP {{ postcode }} center
            </span>
          </span>
          <span class="hotel-card-map-cue">Show on map</span>
        </button>
        <a
          class="hotel-card-google-link"
          :href="googleMapsUrl(hotel)"
          target="_blank"
          rel="noopener noreferrer"
          :aria-label="`${googleMapsLabel(hotel)} for ${hotel.name || 'this hotel'} (opens in a new tab)`"
        >
          {{ googleMapsLabel(hotel) }}
          <span aria-hidden="true">↗</span>
        </a>
      </article>
    </li>
  </ol>
</template>
