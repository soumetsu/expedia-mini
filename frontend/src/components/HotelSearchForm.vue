<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, required: true },
  checkIn: { type: String, default: '' },
  checkOut: { type: String, default: '' },
  users: { type: Array, required: true },
  selectedUserId: { type: String, required: true },
  loading: { type: Boolean, required: true },
})

const emit = defineEmits([
  'update:modelValue',
  'update:checkIn',
  'update:checkOut',
  'update:selectedUserId',
  'search',
])
const validationMessage = ref('')
const input = ref(null)

function updateLocation(event) {
  emit('update:modelValue', event.target.value)
  if (event.target.value.trim()) validationMessage.value = ''
}

function submitSearch() {
  const location = props.modelValue.trim()

  if (!location) {
    validationMessage.value = 'Enter a city, state, or hotel name.'
    input.value?.focus()
    return
  }

  if (props.checkIn && props.checkOut && props.checkOut <= props.checkIn) {
    validationMessage.value = 'Check-out must be after check-in.'
    return
  }

  validationMessage.value = ''
  emit('update:modelValue', location)
  emit('search', { location, checkIn: props.checkIn, checkOut: props.checkOut })
}
</script>

<template>
  <form class="search-form" :aria-busy="loading" novalidate @submit.prevent="submitSearch">
    <div class="primary-search-row">
      <div class="form-field">
        <label for="location-search">Where do you want to stay?</label>
        <div class="search-input-wrap">
          <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22">
            <path
              d="m21 21-4.35-4.35m1.35-5.15a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0Z"
              fill="none"
              stroke="currentColor"
              stroke-linecap="round"
              stroke-width="2"
            />
          </svg>
          <input
            id="location-search"
            ref="input"
            name="location"
            type="search"
            autocomplete="off"
            placeholder="Try Boston, New York, or PA"
            :value="modelValue"
            :disabled="loading"
            :aria-invalid="Boolean(validationMessage)"
            :aria-describedby="validationMessage ? 'search-error' : 'location-hint'"
            @input="updateLocation"
          />
        </div>
        <p id="location-hint" class="field-hint">Search by city, state, or hotel name.</p>
      </div>

      <button class="primary-action" type="submit" :disabled="loading">
        {{ loading ? 'Finding stays…' : 'Find stays' }}
      </button>
    </div>

    <div class="search-details-row" aria-label="Optional trip details">
      <div class="compact-field">
        <label for="check-in">Check-in <span>optional</span></label>
        <input
          id="check-in"
          name="check-in"
          type="date"
          :value="checkIn"
          :disabled="loading"
          @input="emit('update:checkIn', $event.target.value)"
        />
      </div>
      <div class="compact-field">
        <label for="check-out">Check-out <span>optional</span></label>
        <input
          id="check-out"
          name="check-out"
          type="date"
          :value="checkOut"
          :disabled="loading"
          @input="emit('update:checkOut', $event.target.value)"
        />
      </div>
      <div class="compact-field">
        <label for="demo-traveler">Booking traveler</label>
        <select
          id="demo-traveler"
          :value="selectedUserId"
          :disabled="loading || !users.length"
          @change="emit('update:selectedUserId', $event.target.value)"
        >
          <option v-for="user in users" :key="user.user_id" :value="user.user_id">
            {{ user.display_name }}
          </option>
        </select>
      </div>
    </div>

    <p class="fixed-date-note">Dates narrow the supplied fixed-date stay catalog.</p>
    <p v-if="validationMessage" id="search-error" class="field-error" role="alert">
      {{ validationMessage }}
    </p>
  </form>
</template>
