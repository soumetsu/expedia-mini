<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, required: true },
  loading: { type: Boolean, required: true },
})

const emit = defineEmits(['update:modelValue', 'clear', 'search'])
const validationMessage = ref('')
const input = ref(null)

function updatePostcode(event) {
  const postcode = event.target.value.replace(/\D/g, '').slice(0, 5)
  emit('update:modelValue', postcode)
  if (/^\d{5}$/.test(postcode)) validationMessage.value = ''
}

function submitSearch() {
  const postcode = props.modelValue.trim()
  if (!/^\d{5}$/.test(postcode)) {
    validationMessage.value = 'Enter a valid 5-digit U.S. ZIP code.'
    input.value?.focus()
    return
  }

  validationMessage.value = ''
  emit('update:modelValue', postcode)
  emit('search', { postcode })
}

function clearSearch() {
  validationMessage.value = ''
  emit('update:modelValue', '')
  emit('clear')
  input.value?.focus()
}
</script>

<template>
  <form class="zip-search-form" :aria-busy="loading" novalidate @submit.prevent="submitSearch">
    <div class="zip-search-row">
      <div class="form-field">
        <label for="postcode-search">U.S. ZIP code</label>
        <div class="zip-search-input-wrap">
          <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22">
            <path
              d="M12 21s6-5.2 6-11A6 6 0 0 0 6 10c0 5.8 6 11 6 11Z"
              fill="none"
              stroke="currentColor"
              stroke-linejoin="round"
              stroke-width="2"
            />
            <circle cx="12" cy="10" r="2" fill="currentColor" />
          </svg>
          <input
            id="postcode-search"
            ref="input"
            name="postcode"
            type="text"
            inputmode="numeric"
            autocomplete="postal-code"
            maxlength="5"
            placeholder="Example: 16802"
            :value="modelValue"
            :disabled="loading"
            :aria-invalid="Boolean(validationMessage)"
            :aria-describedby="validationMessage ? 'postcode-error' : 'postcode-hint'"
            @input="updatePostcode"
          />
        </div>
        <p id="postcode-hint" class="field-hint">
          Geoapify searches the ZIP boundary first, then expands to 5, 15, or 30 miles only if
          needed.
        </p>
      </div>

      <button class="live-search-action" type="submit" :disabled="loading">
        {{ loading ? 'Finding hotels…' : 'Search live hotels' }}
      </button>
    </div>

    <div class="zip-search-footer">
      <p>Distances are straight-line estimates from the ZIP code’s reference center.</p>
      <button class="clear-action clear-action--dark" type="button" :disabled="loading" @click="clearSearch">
        Clear ZIP
      </button>
    </div>
    <p v-if="validationMessage" id="postcode-error" class="field-error field-error--light" role="alert">
      {{ validationMessage }}
    </p>
  </form>
</template>
