<script setup>
import { nextTick, ref } from 'vue'

import { sendChatMessage } from '../services/api.js'

const CHAT_MODEL = 'gemini-3.5-flash-lite'

const isOpen = ref(false)
const isExpanded = ref(false)
const draft = ref('')
const isPending = ref(false)
const errorMessage = ref('')
const conversation = ref(null)
const messageField = ref(null)
const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: 'Hi! I can help you use Expedia-Mini search, saved hotels, and the booking sandbox.',
    localOnly: true,
  },
])
let nextMessageId = 2

async function scrollToLatest() {
  await nextTick()
  if (conversation.value) conversation.value.scrollTop = conversation.value.scrollHeight
}

async function openChat() {
  isOpen.value = true
  await nextTick()
  messageField.value?.focus()
}

function closeChat() {
  isOpen.value = false
  isExpanded.value = false
}

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
  scrollToLatest()
}

async function submitMessage() {
  const message = draft.value.trim()
  if (!message || isPending.value) return

  const history = messages.value
    .filter((item) => item.includeInHistory)
    .slice(-10)
    .map((item) => ({ role: item.role, content: item.content }))

  const userMessage = {
    id: nextMessageId++,
    role: 'user',
    content: message,
    includeInHistory: false,
  }
  messages.value.push(userMessage)
  draft.value = ''
  errorMessage.value = ''
  isPending.value = true
  await scrollToLatest()

  try {
    const response = await sendChatMessage(message, history)
    userMessage.includeInHistory = true
    messages.value.push({
      id: nextMessageId++,
      role: 'assistant',
      content: response.reply,
      model: response.model,
      usage: response.usage,
      includeInHistory: true,
    })
  } catch (error) {
    errorMessage.value = error.message || 'The support chatbot could not reply.'
  } finally {
    isPending.value = false
    await scrollToLatest()
    messageField.value?.focus()
  }
}
</script>

<template>
  <div class="support-chatbot" :class="{ 'support-chatbot-expanded': isExpanded }">
    <button
      v-if="!isOpen"
      class="support-chat-launcher"
      type="button"
      aria-haspopup="dialog"
      @click="openChat"
    >
      <span class="support-chat-icon" aria-hidden="true">💬</span>
      <span>Support / Chatbot</span>
    </button>

    <section
      v-else
      class="support-chat-panel"
      role="dialog"
      aria-modal="false"
      aria-labelledby="support-chat-title"
      @keydown.esc="closeChat"
    >
      <header class="support-chat-header">
        <div>
          <p class="support-chat-kicker">Gemini support</p>
          <h2 id="support-chat-title">How can I help?</h2>
          <p class="support-chat-model">Model: {{ CHAT_MODEL }}</p>
        </div>
        <div class="support-chat-window-actions">
          <button
            type="button"
            :aria-label="isExpanded ? 'Restore chatbot size' : 'Expand chatbot'"
            :aria-pressed="isExpanded"
            @click="toggleExpanded"
          >
            {{ isExpanded ? 'Restore' : 'Expand' }}
          </button>
          <button type="button" aria-label="Close chatbot" @click="closeChat">Close</button>
        </div>
      </header>

      <div ref="conversation" class="support-chat-conversation" role="log" aria-live="polite">
        <article
          v-for="message in messages"
          :key="message.id"
          class="support-chat-message"
          :class="`support-chat-message-${message.role}`"
        >
          <span>{{ message.role === 'user' ? 'You' : 'Support' }}</span>
          <p>{{ message.content }}</p>
          <p v-if="message.usage" class="support-chat-usage">
            Tokens: {{ message.usage.prompt_tokens }} input +
            {{ message.usage.response_tokens }} output =
            {{ message.usage.total_tokens }} total
          </p>
        </article>
        <article v-if="isPending" class="support-chat-message support-chat-message-assistant">
          <span>Support</span>
          <p>Thinking…</p>
        </article>
      </div>

      <p v-if="errorMessage" class="support-chat-error" role="alert">
        {{ errorMessage }} You can try sending the message again.
      </p>

      <form class="support-chat-form" @submit.prevent="submitMessage">
        <label class="visually-hidden" for="support-chat-message">Message support</label>
        <textarea
          id="support-chat-message"
          ref="messageField"
          v-model="draft"
          rows="2"
          maxlength="2000"
          placeholder="Ask how to use Expedia-Mini…"
          :disabled="isPending"
          @keydown.enter.exact.prevent="submitMessage"
        />
        <button type="submit" :disabled="isPending || !draft.trim()">
          {{ isPending ? 'Sending…' : 'Send' }}
        </button>
      </form>
      <p class="support-chat-disclaimer">
        Support answers may be inaccurate. Live hotel availability and prices are not provided.
      </p>
    </section>
  </div>
</template>
