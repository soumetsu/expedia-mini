<script setup>
import { ref, watch } from 'vue'

import { cancelBooking, deleteBooking, getBookingHistory } from '../services/api.js'

const props = defineProps({
  users: { type: Array, required: true },
  selectedUserId: { type: String, required: true },
})
const emit = defineEmits(['update:selectedUserId', 'navigate'])

const bookings = ref([])
const loading = ref(false)
const errorMessage = ref('')
const actionBookingId = ref('')
const deleteConfirmationId = ref('')

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

function formatDate(value) {
  return dateFormatter.format(new Date(`${value}T00:00:00Z`))
}

function formatStatus(value) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

async function loadBookings() {
  if (!props.selectedUserId) return
  loading.value = true
  errorMessage.value = ''
  deleteConfirmationId.value = ''
  try {
    bookings.value = await getBookingHistory(props.selectedUserId)
  } catch (error) {
    errorMessage.value = error.message || 'Booking history could not be loaded.'
  } finally {
    loading.value = false
  }
}

async function handleCancel(booking) {
  actionBookingId.value = booking.booking_id
  errorMessage.value = ''
  try {
    const updated = await cancelBooking(booking.booking_id)
    bookings.value = bookings.value.map((item) =>
      item.booking_id === updated.booking_id ? updated : item,
    )
  } catch (error) {
    errorMessage.value = error.message || 'The booking could not be cancelled.'
  } finally {
    actionBookingId.value = ''
  }
}

async function handleDelete(booking) {
  actionBookingId.value = booking.booking_id
  errorMessage.value = ''
  try {
    await deleteBooking(booking.booking_id)
    bookings.value = bookings.value.filter((item) => item.booking_id !== booking.booking_id)
    deleteConfirmationId.value = ''
  } catch (error) {
    errorMessage.value = error.message || 'The test booking could not be deleted.'
  } finally {
    actionBookingId.value = ''
  }
}

watch(() => props.selectedUserId, loadBookings, { immediate: true })
</script>

<template>
  <main>
    <header class="subpage-hero">
      <div class="page-container subpage-hero-inner">
        <p class="eyebrow">Your trips</p>
        <h1>Booking history</h1>
        <p>Review every simulated reservation, cancel one while keeping its record, or remove a test booking.</p>
      </div>
    </header>

    <div class="page-container history-page">
      <section class="history-toolbar" aria-labelledby="history-title">
        <div>
          <p class="eyebrow">Demo account</p>
          <h2 id="history-title">Saved reservations</h2>
        </div>
        <div class="traveler-select">
          <label for="history-traveler">Traveler</label>
          <select
            id="history-traveler"
            :value="selectedUserId"
            :disabled="loading || !users.length"
            @change="emit('update:selectedUserId', $event.target.value)"
          >
            <option v-for="user in users" :key="user.user_id" :value="user.user_id">
              {{ user.display_name }}
            </option>
          </select>
        </div>
      </section>

      <div class="history-status" aria-live="polite">
        <p v-if="loading" role="status">Loading booking history…</p>
        <p v-else-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
      </div>

      <section v-if="!loading && bookings.length" class="booking-list" aria-label="Bookings">
        <article v-for="booking in bookings" :key="booking.booking_id" class="booking-card">
          <div class="booking-card-heading">
            <div>
              <p class="booking-kicker">Booking {{ booking.booking_id }} · Stay {{ booking.trip_id }}</p>
              <h3>{{ booking.hotel_name }}</h3>
              <p>{{ booking.city }}, {{ booking.state }} · {{ booking.trip_name }}</p>
            </div>
            <span class="status-badge" :class="booking.status.toLowerCase()">
              {{ formatStatus(booking.status) }}
            </span>
          </div>

          <dl class="booking-facts">
            <div>
              <dt>Dates</dt>
              <dd>{{ formatDate(booking.check_in) }} – {{ formatDate(booking.check_out) }}</dd>
            </div>
            <div>
              <dt>Length</dt>
              <dd>{{ booking.nights }} nights</dd>
            </div>
            <div>
              <dt>Estimated total</dt>
              <dd>{{ usdFormatter.format(Number(booking.estimated_stay_price_usd)) }}</dd>
            </div>
          </dl>

          <div class="booking-actions">
            <button
              v-if="booking.status === 'confirmed'"
              class="secondary-action"
              type="button"
              :disabled="Boolean(actionBookingId)"
              @click="handleCancel(booking)"
            >
              {{ actionBookingId === booking.booking_id ? 'Cancelling…' : 'Cancel booking' }}
            </button>

            <template v-if="booking.can_delete">
              <button
                v-if="deleteConfirmationId !== booking.booking_id"
                class="danger-action"
                type="button"
                :disabled="Boolean(actionBookingId)"
                @click="deleteConfirmationId = booking.booking_id"
              >
                Delete test booking
              </button>
              <div v-else class="delete-confirmation" role="group" aria-label="Confirm deletion">
                <span>Delete this test record?</span>
                <button
                  class="danger-action danger-action--solid"
                  type="button"
                  :disabled="Boolean(actionBookingId)"
                  @click="handleDelete(booking)"
                >
                  {{ actionBookingId === booking.booking_id ? 'Deleting…' : 'Yes, delete' }}
                </button>
                <button class="text-action" type="button" @click="deleteConfirmationId = ''">
                  Keep it
                </button>
              </div>
            </template>
            <p v-else class="seed-note">Seeded example · retained for the demo</p>
          </div>
        </article>
      </section>

      <section v-else-if="!loading && !errorMessage" class="empty-history">
        <span aria-hidden="true">⌁</span>
        <h2>No bookings for this traveler yet</h2>
        <p>Find a stay, choose “Book this stay,” and it will appear here.</p>
        <button class="primary-action" type="button" @click="emit('navigate', '/')">
          Search available stays
        </button>
      </section>
    </div>
  </main>
</template>
