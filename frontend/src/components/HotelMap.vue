<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  results: { type: Array, required: true },
  center: { type: Object, required: true },
  selectedPlaceId: { type: String, default: '' },
  resultSource: { type: String, default: 'api' },
})

const emit = defineEmits(['select'])
const mapElement = ref(null)
let map = null
let hotelLayer = null
let centerLayer = null
const markers = new Map()

function hotelIcon(index, selected = false) {
  return L.divIcon({
    className: `hotel-map-marker${selected ? ' hotel-map-marker--selected' : ''}`,
    html: `<span aria-hidden="true">${index + 1}</span>`,
    iconSize: selected ? [38, 38] : [32, 32],
    iconAnchor: selected ? [19, 38] : [16, 32],
  })
}

function safeHotelTooltip(hotel) {
  const wrapper = document.createElement('div')
  const name = document.createElement('strong')
  const distance = document.createElement('span')
  name.textContent = hotel.name || 'Name unavailable'
  distance.textContent = `${hotel.distance_miles.toFixed(1)} mi from ZIP center`
  wrapper.append(name, document.createElement('br'), distance)
  return wrapper
}

function focusSelected(animate = true) {
  if (!map) return
  markers.forEach(({ marker, index }, placeId) => {
    const selected = placeId === props.selectedPlaceId
    marker.setIcon(hotelIcon(index, selected))
    marker.setZIndexOffset(selected ? 1000 : 0)
  })

  const selectedEntry = markers.get(props.selectedPlaceId)
  if (!selectedEntry) return
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (animate && !reduceMotion) {
    map.flyTo(selectedEntry.marker.getLatLng(), Math.max(map.getZoom(), 15), {
      duration: 0.45,
    })
  } else {
    map.panInside(selectedEntry.marker.getLatLng(), { padding: [56, 56] })
  }
  selectedEntry.marker.openTooltip()
}

function renderLocations() {
  if (!map) return
  hotelLayer.clearLayers()
  markers.clear()
  if (centerLayer) centerLayer.remove()

  const center = [props.center.latitude, props.center.longitude]
  centerLayer = L.circleMarker(center, {
    radius: 7,
    color: '#ffffff',
    weight: 3,
    fillColor: '#123f67',
    fillOpacity: 1,
  })
    .bindTooltip(`ZIP ${props.center.postcode} center`, { direction: 'top' })
    .addTo(map)

  const bounds = L.latLngBounds([center])
  props.results.forEach((hotel, index) => {
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      icon: hotelIcon(index, hotel.place_id === props.selectedPlaceId),
      keyboard: true,
      riseOnHover: true,
      title: hotel.name || 'Name unavailable',
      alt: `${hotel.name || 'Unnamed hotel'}, result ${index + 1}`,
    })
    marker.bindTooltip(safeHotelTooltip(hotel), { direction: 'top', opacity: 1 })
    marker.on('click', () => emit('select', hotel.place_id))
    marker.addTo(hotelLayer)
    markers.set(hotel.place_id, { marker, index })
    bounds.extend([hotel.latitude, hotel.longitude])
  })

  map.fitBounds(bounds.pad(0.16), { padding: [28, 28], maxZoom: 15 })
  window.setTimeout(() => map?.invalidateSize({ pan: false }), 0)
  focusSelected(false)
}

onMounted(() => {
  map = L.map(mapElement.value, {
    zoomControl: true,
    scrollWheelZoom: true,
  })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)
  hotelLayer = L.layerGroup().addTo(map)
  renderLocations()
})

watch(() => [props.results, props.center], renderLocations)
watch(() => props.selectedPlaceId, () => focusSelected(true))

onBeforeUnmount(() => {
  map?.remove()
  map = null
  markers.clear()
})
</script>

<template>
  <div class="hotel-map-shell">
    <div
      ref="mapElement"
      class="hotel-map"
      :aria-label="
        resultSource === 'local'
          ? 'Interactive map of locally saved hotel results'
          : 'Interactive map of live API hotel results'
      "
    ></div>
    <p class="hotel-map-note">Map imagery © OpenStreetMap contributors.</p>
  </div>
</template>
