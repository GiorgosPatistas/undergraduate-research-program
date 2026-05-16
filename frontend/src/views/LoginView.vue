<template>
  <div class="min-h-[calc(100vh-8rem)] flex items-center justify-center px-6 py-16">
    <div class="w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-10">
        <h1 class="text-4xl font-display font-semibold text-white mb-2">Welcome back</h1>
        <p class="text-slate-400">Sign in to access the prediction system.</p>
      </div>

      <!-- Card -->
      <div class="card">
        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- Username -->
          <div>
            <label class="form-label" for="username">Username</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="form-input"
              placeholder="your_username"
              autocomplete="username"
              required
            />
          </div>

          <!-- Password -->
          <div>
            <label class="form-label" for="password">Password</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="••••••••"
              autocomplete="current-password"
              required
            />
          </div>

          <!-- Error message -->
          <div v-if="auth.error" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">
            {{ auth.error }}
          </div>

          <!-- Submit -->
          <button
            type="submit"
            class="btn-primary w-full justify-center py-3"
            :disabled="auth.loading"
          >
            <span v-if="auth.loading" class="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
            <span>{{ auth.loading ? 'Signing in…' : 'Sign in' }}</span>
          </button>
        </form>
      </div>

      <!-- Register link -->
      <p class="text-center text-slate-400 mt-6 text-sm">
        Don't have an account?
        <RouterLink to="/register" class="text-crimson-400 hover:text-crimson-300 font-medium ml-1">
          Create one
        </RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const form = reactive({
  username: '',
  password: ''
})

async function handleLogin() {
  try {
    await auth.login(form.username, form.password)
  } catch {
    // error is handled in the store
  }
}
</script>
