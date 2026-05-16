<template>
  <div class="max-w-3xl mx-auto px-6 py-12">

    <!-- ══════════════════════════════════════════════
         DOCTOR PROFILE
    ══════════════════════════════════════════════ -->
    <template v-if="auth.isDoctor">

      <!-- Header -->
      <div class="mb-10">
        <span class="badge badge-blue mb-3">Doctor Portal</span>
        <h1 class="text-4xl font-display font-semibold text-white mb-2">
          {{ auth.user?.full_name || auth.user?.username }}
        </h1>
        <p class="text-slate-400">{{ auth.user?.specialty || 'Doctor' }}</p>
      </div>

      <!-- Profile card -->
      <div class="card mb-6">
        <div class="flex items-center gap-5 mb-6">
          <div class="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center text-3xl flex-shrink-0">
            👨‍⚕️
          </div>
          <div>
            <h2 class="text-xl font-semibold text-white">{{ auth.user?.full_name || auth.user?.username }}</h2>
            <span class="badge badge-blue text-xs mt-1">{{ auth.user?.specialty || 'Doctor' }}</span>
          </div>
        </div>
        <div class="grid sm:grid-cols-2 gap-4 pt-4 border-t border-navy-700">
          <div>
            <div class="text-xs text-slate-500 uppercase tracking-wider mb-1">Username</div>
            <div class="text-white font-medium">{{ auth.user?.username }}</div>
          </div>
          <div>
            <div class="text-xs text-slate-500 uppercase tracking-wider mb-1">Email</div>
            <div class="text-white font-medium">{{ auth.user?.email || '—' }}</div>
          </div>
        </div>
      </div>

      <!-- Appointment stats -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="card text-center">
          <div class="text-3xl font-bold text-white mb-1">{{ apptStats.total }}</div>
          <div class="text-xs text-slate-400 uppercase tracking-wider">Total</div>
        </div>
        <div class="card text-center">
          <div class="text-3xl font-bold text-emerald-400 mb-1">{{ apptStats.confirmed }}</div>
          <div class="text-xs text-slate-400 uppercase tracking-wider">Confirmed</div>
        </div>
        <div class="card text-center">
          <div class="text-3xl font-bold text-amber-400 mb-1">{{ apptStats.pending }}</div>
          <div class="text-xs text-slate-400 uppercase tracking-wider">Pending</div>
        </div>
      </div>

      <!-- Appointment history -->
      <div class="card mb-6">
        <h3 class="text-lg font-semibold text-white mb-5">Appointment History</h3>

        <div v-if="apptLoading" class="text-slate-400 text-sm text-center py-6">Loading…</div>

        <div v-else-if="!appointments.length" class="text-slate-500 text-sm text-center py-6">
          No appointments yet.
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="appt in appointments"
            :key="appt.id"
            class="flex items-center justify-between py-3 border-b border-navy-700 last:border-0"
          >
            <div>
              <div class="text-white font-medium text-sm">{{ appt.patient_name }}</div>
              <div class="text-slate-400 text-xs">{{ appt.patient_email }}</div>
            </div>
            <div class="text-center text-sm text-slate-300">
              <div>{{ formatDate(appt.date) }}</div>
              <div class="text-slate-500 text-xs">{{ appt.time }}</div>
            </div>
            <span
              class="badge text-xs"
              :class="{
                'badge-blue':  appt.status === 'pending',
                'badge-green': appt.status === 'confirmed',
                'badge-red':   appt.status === 'cancelled',
              }"
            >
              {{ appt.status }}
            </span>
          </div>
        </div>
      </div>

      <!-- Change Password -->
      <div class="card mb-6">
        <h3 class="text-lg font-semibold text-white mb-5">Change Password</h3>
        <form @submit.prevent="handlePasswordChange" class="space-y-4">
          <div>
            <label class="form-label">Current Password</label>
            <input v-model="passwordForm.current" type="password" class="form-input"
              placeholder="••••••••" autocomplete="current-password" required />
          </div>
          <div>
            <label class="form-label">New Password</label>
            <input v-model="passwordForm.new_password" type="password" class="form-input"
              placeholder="••••••••" autocomplete="new-password" required minlength="8" />
          </div>
          <div>
            <label class="form-label">Confirm New Password</label>
            <input v-model="passwordForm.confirm" type="password" class="form-input"
              placeholder="••••••••" autocomplete="new-password" required />
            <p v-if="passwordMismatch" class="text-crimson-400 text-xs mt-1">Passwords do not match.</p>
          </div>
          <div v-if="passwordError" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">{{ passwordError }}</div>
          <div v-if="passwordSuccess" class="rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-emerald-300 text-sm">✓ Password updated successfully.</div>
          <button type="submit" class="btn-primary py-2.5" :disabled="passwordLoading || passwordMismatch">
            {{ passwordLoading ? 'Updating…' : 'Update Password' }}
          </button>
        </form>
      </div>

      <!-- Sign out -->
      <div class="rounded-xl border border-crimson-500/30 bg-crimson-500/5 p-6">
        <h3 class="font-semibold text-crimson-400 mb-1">Sign Out</h3>
        <p class="text-slate-400 text-sm mb-4">You will be redirected to the login page.</p>
        <button @click="auth.logout()" class="btn-secondary text-sm py-2 border-crimson-500/40 hover:bg-crimson-500/10">
          Sign out of account
        </button>
      </div>

    </template>

    <!-- ══════════════════════════════════════════════
         PATIENT PROFILE
    ══════════════════════════════════════════════ -->
    <template v-else-if="auth.isPatient">

      <!-- Header -->
      <div class="mb-10">
        <span class="badge badge-red mb-3">Patient Portal</span>
        <h1 class="text-4xl font-display font-semibold text-white mb-2">
          {{ auth.user?.username }}
        </h1>
        <p class="text-slate-400">{{ auth.user?.email }}</p>
      </div>

      <!-- Profile card -->
      <div class="card mb-6">
        <div class="flex items-center gap-5 mb-6">
          <div class="w-16 h-16 rounded-full bg-crimson-500/20 flex items-center justify-center text-3xl flex-shrink-0">
            🧑‍⚕️
          </div>
          <div>
            <h2 class="text-xl font-semibold text-white">{{ auth.user?.username }}</h2>
            <span class="badge badge-red text-xs mt-1">Patient</span>
          </div>
        </div>
        <div class="grid sm:grid-cols-2 gap-4 pt-4 border-t border-navy-700">
          <div>
            <div class="text-xs text-slate-500 uppercase tracking-wider mb-1">Username</div>
            <div class="text-white font-medium">{{ auth.user?.username }}</div>
          </div>
          <div>
            <div class="text-xs text-slate-500 uppercase tracking-wider mb-1">Email</div>
            <div class="text-white font-medium">{{ auth.user?.email || '—' }}</div>
          </div>
        </div>
      </div>

      <!-- Prediction history -->
      <div class="card mb-6">
        <h3 class="text-lg font-semibold text-white mb-5">Prediction History</h3>

        <div v-if="predLoading" class="text-slate-400 text-sm text-center py-6">Loading…</div>

        <div v-else-if="!predictions.length" class="text-slate-500 text-sm text-center py-6">
          No predictions yet.
          <RouterLink to="/services" class="text-crimson-400 hover:underline ml-1">Run your first prediction →</RouterLink>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="pred in predictions"
            :key="pred.id"
            class="flex items-center justify-between py-3 border-b border-navy-700 last:border-0"
          >
            <div class="flex items-center gap-3">
              <span class="badge text-xs" :class="pred.prediction ? 'badge-red' : 'badge-green'">
                {{ pred.prediction ? '⚠ High Risk' : '✓ Low Risk' }}
              </span>
              <span class="text-slate-400 text-xs font-mono">
                {{ (pred.probability * 100).toFixed(1) }}% readmission risk
              </span>
            </div>
            <div class="text-slate-500 text-xs">{{ formatDate(pred.created_at) }}</div>
          </div>
        </div>
      </div>

      <!-- Appointment history -->
      <div class="card mb-6">
        <h3 class="text-lg font-semibold text-white mb-5">My Appointments</h3>

        <div v-if="apptLoading" class="text-slate-400 text-sm text-center py-6">Loading…</div>

        <div v-else-if="!appointments.length" class="text-slate-500 text-sm text-center py-6">
          No appointments booked yet.
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="appt in appointments"
            :key="appt.id"
            class="flex items-center justify-between py-3 border-b border-navy-700 last:border-0"
          >
            <div>
              <div class="text-white font-medium text-sm">Dr. {{ appt.doctor_name }}</div>
              <div class="text-slate-400 text-xs">{{ formatDate(appt.date) }} · {{ appt.time }}</div>
            </div>
            <span
              class="badge text-xs"
              :class="{
                'badge-blue':  appt.status === 'pending',
                'badge-green': appt.status === 'confirmed',
                'badge-red':   appt.status === 'cancelled',
              }"
            >
              {{ appt.status }}
            </span>
          </div>
        </div>
      </div>

      <!-- Change Password -->
      <div class="card mb-6">
        <h3 class="text-lg font-semibold text-white mb-5">Change Password</h3>
        <form @submit.prevent="handlePasswordChange" class="space-y-4">
          <div>
            <label class="form-label">Current Password</label>
            <input v-model="passwordForm.current" type="password" class="form-input"
              placeholder="••••••••" autocomplete="current-password" required />
          </div>
          <div>
            <label class="form-label">New Password</label>
            <input v-model="passwordForm.new_password" type="password" class="form-input"
              placeholder="••••••••" autocomplete="new-password" required minlength="8" />
          </div>
          <div>
            <label class="form-label">Confirm New Password</label>
            <input v-model="passwordForm.confirm" type="password" class="form-input"
              placeholder="••••••••" autocomplete="new-password" required />
            <p v-if="passwordMismatch" class="text-crimson-400 text-xs mt-1">Passwords do not match.</p>
          </div>
          <div v-if="passwordError" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">{{ passwordError }}</div>
          <div v-if="passwordSuccess" class="rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-emerald-300 text-sm">✓ Password updated successfully.</div>
          <button type="submit" class="btn-primary py-2.5" :disabled="passwordLoading || passwordMismatch">
            {{ passwordLoading ? 'Updating…' : 'Update Password' }}
          </button>
        </form>
      </div>

      <!-- Sign out -->
      <div class="rounded-xl border border-crimson-500/30 bg-crimson-500/5 p-6">
        <h3 class="font-semibold text-crimson-400 mb-1">Sign Out</h3>
        <p class="text-slate-400 text-sm mb-4">You will be redirected to the login page.</p>
        <button @click="auth.logout()" class="btn-secondary text-sm py-2 border-crimson-500/40 hover:bg-crimson-500/10">
          Sign out of account
        </button>
      </div>

    </template>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const auth = useAuthStore()

// ── Data ───────────────────────────────────────────────────────────────────────
const apptLoading  = ref(false)
const appointments = ref([])

const predLoading  = ref(false)
const predictions  = ref([])

// ── Fetch ──────────────────────────────────────────────────────────────────────
async function loadAppointments() {
  apptLoading.value = true
  try {
    const { data } = await api.get('/appointments/')
    appointments.value = data
  } finally {
    apptLoading.value = false
  }
}

async function loadPredictions() {
  predLoading.value = true
  try {
    const { data } = await api.get('/predictions/')
    predictions.value = data
  } finally {
    predLoading.value = false
  }
}

onMounted(() => {
  loadAppointments()
  if (auth.isPatient) loadPredictions()
})

// ── Doctor stats ───────────────────────────────────────────────────────────────
const apptStats = computed(() => ({
  total:     appointments.value.length,
  confirmed: appointments.value.filter(a => a.status === 'confirmed').length,
  pending:   appointments.value.filter(a => a.status === 'pending').length,
}))

// ── Password change (shared) ───────────────────────────────────────────────────
const passwordForm    = reactive({ current: '', new_password: '', confirm: '' })
const passwordLoading = ref(false)
const passwordError   = ref(null)
const passwordSuccess = ref(false)

const passwordMismatch = computed(
  () => passwordForm.confirm.length > 0 && passwordForm.new_password !== passwordForm.confirm
)

async function handlePasswordChange() {
  if (passwordMismatch.value) return
  passwordLoading.value = true
  passwordError.value   = null
  passwordSuccess.value = false
  try {
    await api.post('/auth/change-password/', {
      current_password: passwordForm.current,
      new_password:     passwordForm.new_password,
    })
    passwordSuccess.value = true
    passwordForm.current = passwordForm.new_password = passwordForm.confirm = ''
  } catch (err) {
    passwordError.value = err.response?.data?.detail || 'Failed to update password.'
  } finally {
    passwordLoading.value = false
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>
