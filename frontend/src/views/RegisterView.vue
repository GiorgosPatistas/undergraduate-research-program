<template>
  <div class="min-h-[calc(100vh-8rem)] flex items-center justify-center px-6 py-16">
    <div class="w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-10">
        <h1 class="text-4xl font-display font-semibold text-white mb-2">Create account</h1>
        <p class="text-slate-400">Join the Smart Healthcare platform.</p>
      </div>

      <!-- Role selector -->
      <div class="grid grid-cols-2 gap-3 mb-6">
        <button
          type="button"
          @click="form.role = 'patient'"
          class="flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200"
          :class="form.role === 'patient'
            ? 'border-crimson-500 bg-crimson-500/10 text-white'
            : 'border-navy-600 bg-navy-800 text-slate-400 hover:border-navy-500'"
        >
          <span class="text-3xl">🧑‍⚕️</span>
          <span class="font-medium text-sm">Patient</span>
          <span class="text-xs text-center leading-tight opacity-70">Run predictions & book appointments</span>
        </button>
        <button
          type="button"
          @click="form.role = 'doctor'"
          class="flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200"
          :class="form.role === 'doctor'
            ? 'border-crimson-500 bg-crimson-500/10 text-white'
            : 'border-navy-600 bg-navy-800 text-slate-400 hover:border-navy-500'"
        >
          <span class="text-3xl">👨‍⚕️</span>
          <span class="font-medium text-sm">Doctor</span>
          <span class="text-xs text-center leading-tight opacity-70">Manage patients & publish articles</span>
        </button>
      </div>

      <!-- Card -->
      <div class="card">
        <form @submit.prevent="handleRegister" class="space-y-5">
          <div>
            <label class="form-label" for="username">Username</label>
            <input id="username" v-model="form.username" type="text" class="form-input"
              placeholder="your_username" autocomplete="username" required minlength="3" />
          </div>

          <div>
            <label class="form-label" for="email">Email</label>
            <input id="email" v-model="form.email" type="email" class="form-input"
              placeholder="you@example.com" autocomplete="email" required />
          </div>

          <!-- Doctor-only: full name & specialty -->
          <template v-if="form.role === 'doctor'">
            <div>
              <label class="form-label" for="fullname">Full Name</label>
              <input id="fullname" v-model="form.full_name" type="text" class="form-input"
                placeholder="Dr. John Smith" required />
            </div>
            <div>
              <label class="form-label" for="specialty">Specialty</label>
              <select id="specialty" v-model="form.specialty" class="form-input" required>
                <option value="" disabled>Select specialty…</option>
                <option v-for="s in specialties" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </template>

          <div>
            <label class="form-label" for="password">Password</label>
            <input id="password" v-model="form.password" type="password" class="form-input"
              placeholder="••••••••" autocomplete="new-password" required minlength="8" />
          </div>

          <div>
            <label class="form-label" for="confirm">Confirm Password</label>
            <input id="confirm" v-model="form.confirm" type="password" class="form-input"
              placeholder="••••••••" autocomplete="new-password" required />
            <p v-if="passwordMismatch" class="text-crimson-400 text-xs mt-1">Passwords do not match.</p>
          </div>

          <div v-if="auth.error" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">
            {{ auth.error }}
          </div>

          <button type="submit" class="btn-primary w-full justify-center py-3"
            :disabled="auth.loading || passwordMismatch || !form.role">
            <span v-if="auth.loading" class="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
            <span>{{ auth.loading ? 'Creating account…' : 'Create account' }}</span>
          </button>
        </form>
      </div>

      <p class="text-center text-slate-400 mt-6 text-sm">
        Already have an account?
        <RouterLink to="/login" class="text-crimson-400 hover:text-crimson-300 font-medium ml-1">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const form = reactive({
  role: 'patient',
  username: '',
  email: '',
  full_name: '',
  specialty: '',
  password: '',
  confirm: ''
})

const specialties = [
  'General Practitioner', 'Endocrinologist', 'Cardiologist',
  'Internist', 'Nephrologist', 'Diabetologist', 'Other'
]

const passwordMismatch = computed(
  () => form.confirm.length > 0 && form.password !== form.confirm
)

async function handleRegister() {
  if (passwordMismatch.value || !form.role) return
  try {
    await auth.register({
      username: form.username,
      email: form.email,
      password: form.password,
      role: form.role,
      full_name: form.full_name || undefined,
      specialty: form.specialty || undefined
    })
  } catch { /* handled in store */ }
}
</script>
