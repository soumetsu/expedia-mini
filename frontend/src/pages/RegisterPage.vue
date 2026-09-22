<script setup>
import { computed, ref } from 'vue'

import { registerAccount } from '../services/api.js'

const emit = defineEmits(['authenticated', 'navigate'])
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const email = ref('')
const loading = ref(false)
const errorMessage = ref('')
const passwordMismatch = computed(
  () => Boolean(confirmPassword.value) && password.value !== confirmPassword.value,
)

async function submit() {
  if (passwordMismatch.value) {
    errorMessage.value = 'Passwords must match.'
    return
  }
  errorMessage.value = ''
  loading.value = true
  try {
    const session = await registerAccount({
      username: username.value,
      password: password.value,
      email: email.value || null,
    })
    emit('authenticated', session)
  } catch (error) {
    errorMessage.value = error.message || 'The account could not be created.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="account-page">
    <div class="page-container account-layout">
      <section class="account-card" aria-labelledby="register-title">
        <p class="eyebrow">Your travel profile</p>
        <h1 id="register-title">Create your account</h1>
        <p class="account-intro">Use a unique username and password to keep your searches separate from other users.</p>
        <form class="account-form" novalidate @submit.prevent="submit">
          <div class="form-field">
            <label for="register-username">Username</label>
            <input
              id="register-username"
              v-model.trim="username"
              minlength="3"
              maxlength="32"
              autocomplete="username"
              required
            />
            <p class="field-hint">3–32 letters, numbers, dots, underscores, or hyphens.</p>
          </div>
          <div class="form-field">
            <label for="register-email">Email <span>optional</span></label>
            <input
              id="register-email"
              v-model.trim="email"
              type="email"
              autocomplete="email"
              placeholder="you@example.test"
            />
          </div>
          <div class="form-field">
            <label for="register-password">Password</label>
            <input
              id="register-password"
              v-model="password"
              type="password"
              minlength="8"
              autocomplete="new-password"
              required
            />
            <p class="field-hint">At least 8 characters. Passwords are stored as hashes.</p>
          </div>
          <div class="form-field">
            <label for="register-confirm">Confirm password</label>
            <input
              id="register-confirm"
              v-model="confirmPassword"
              type="password"
              autocomplete="new-password"
              :aria-invalid="passwordMismatch"
              required
            />
          </div>
          <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
          <button
            class="primary-action"
            type="submit"
            :disabled="loading || !username || password.length < 8 || !confirmPassword"
          >
            {{ loading ? 'Creating account…' : 'Create account' }}
          </button>
        </form>
        <p class="account-switch">
          Already registered?
          <button class="text-action" type="button" @click="emit('navigate', '/login')">
            Sign in
          </button>
        </p>
      </section>
    </div>
  </main>
</template>
