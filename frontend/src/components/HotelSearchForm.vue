<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue', 'search'])
const validationMessage = ref('')
const input = ref(null)

function updateValue(event) {
  const value = event.target.value
  emit('update:modelValue', value)

  if (value.trim()) {
    validationMessage.value = ''
  }
}

function submitSearch() {
  const normalizedValue = props.modelValue.trim()

  if (!normalizedValue) {
    validationMessage.value = 'Enter a hotel name to search.'
    input.value?.focus()
    return
  }

  validationMessage.value = ''
  emit('update:modelValue', normalizedValue)
  emit('search', normalizedValue)
}
</script>

<template>
  <form class="search-form" :aria-busy="loading" novalidate @submit.prevent="submitSearch">
    <div class="form-field">
      <label for="hotel-name">Hotel name</label>
      <input
        id="hotel-name"
        ref="input"
        name="hotel-name"
        type="search"
        autocomplete="off"
        :value="modelValue"
        :disabled="loading"
        :aria-invalid="Boolean(validationMessage)"
        :aria-describedby="validationMessage ? 'hotel-name-error' : undefined"
        @input="updateValue"
      />
      <p v-if="validationMessage" id="hotel-name-error" class="field-error" role="alert">
        {{ validationMessage }}
      </p>
    </div>

    <button type="submit" :disabled="loading">
      {{ loading ? 'Searching…' : 'Search' }}
    </button>
  </form>
</template>
