<script setup>
import { ref } from 'vue'

import { loginAccount } from '../services/api.js'

const emit = defineEmits(['authenticated', 'navigate'])
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  errorMessage.value = ''
  loading.value = true
  try {
    const session = await loginAccount({ username: username.value, password: password.value })
    emit('authenticated', session)
  } catch (error) {
    errorMessage.value = error.message || 'The account could not be signed in.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="account-page">
    <div class="page-container account-layout">
      <section class="account-card" aria-labelledby="login-title">
        <p class="eyebrow">Welcome back</p>
        <h1 id="login-title">Sign in to Expedia-Mini</h1>
        <p class="account-intro">Keep your search history and simulated stays together across visits.</p>
        <form class="account-form" novalidate @submit.prevent="submit">
          <div class="form-field">
            <label for="login-username">Username</label>
            <input id="login-username" v-model.trim="username" autocomplete="username" required />
          </div>
          <div class="form-field">
            <label for="login-password">Password</label>
            <input
              id="login-password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
            />
          </div>
          <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
          <button class="primary-action" type="submit" :disabled="loading || !username || !password">
            {{ loading ? 'Signing in…' : 'Sign in' }}
          </button>
        </form>
        <p class="account-switch">
          New here?
          <button class="text-action" type="button" @click="emit('navigate', '/register')">
            Create your account
          </button>
        </p>
      </section>
    </div>
  </main>
</template>
