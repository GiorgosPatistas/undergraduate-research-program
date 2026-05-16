<template>
  <div class="max-w-5xl mx-auto px-6 py-12">

    <!-- ════════════════════════════════════════════
         DOCTOR VIEW
    ════════════════════════════════════════════ -->
    <template v-if="auth.isDoctor">
      <div class="mb-10">
        <span class="badge badge-blue mb-3">Doctor Portal</span>
        <h1 class="text-4xl font-display font-semibold text-white mb-2">
          Welcome, {{ auth.user?.full_name || auth.user?.username }}
        </h1>
        <p class="text-slate-400">View your appointments and patient prediction results.</p>
      </div>

      <!-- Clinical Assessment Tool -->
      <div class="card mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-white">Clinical Assessment Tool</h2>
            <p class="text-slate-400 text-sm mt-0.5">Run a readmission risk prediction for a patient.</p>
          </div>
          <button
            @click="showDoctorPredForm = !showDoctorPredForm"
            class="btn-primary text-sm px-4 py-2"
          >
            {{ showDoctorPredForm ? '✕ Close' : '+ Run Prediction' }}
          </button>
        </div>

        <div v-if="showDoctorPredForm" class="mt-6 border-t border-navy-700 pt-6 space-y-5">

          <!-- Result view -->
          <div v-if="predResult" class="space-y-5">
            <div
              class="rounded-xl border p-6 text-center"
              :class="isHighRisk ? 'bg-crimson-500/10 border-crimson-500/40' : 'bg-emerald-500/10 border-emerald-500/40'"
            >
              <div class="text-5xl font-display font-bold mb-2"
                :class="isHighRisk ? 'text-crimson-400' : 'text-emerald-400'">
                {{ (predResult.probability * 100).toFixed(1) }}%
              </div>
              <div class="text-lg font-semibold text-white mb-1">
                {{ isHighRisk ? 'High Readmission Risk' : 'Low Readmission Risk' }}
              </div>
              <span :class="isHighRisk ? 'badge-red' : 'badge-green'" class="badge text-sm px-4 py-1 inline-block">
                {{ isHighRisk ? 'Readmission Predicted' : 'No Readmission Predicted' }}
              </span>
            </div>

            <div v-if="predResult.shap_values">
              <h3 class="text-sm font-semibold text-white mb-3">Top Risk Factors (SHAP)</h3>
              <div class="space-y-2">
                <div
                  v-for="s in sortedShap(predResult.shap_values).slice(0, 6)"
                  :key="s.feature"
                  class="flex items-center gap-3 text-xs"
                >
                  <span class="w-44 truncate text-slate-300 font-mono">{{ s.feature }}</span>
                  <div class="flex-1 h-2 bg-navy-700 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :class="s.value >= 0 ? 'bg-crimson-500' : 'bg-emerald-500'"
                      :style="{ width: Math.min(Math.abs(s.value) * 300, 100) + '%' }"
                    ></div>
                  </div>
                  <span :class="s.value >= 0 ? 'text-crimson-400' : 'text-emerald-400'" class="w-16 text-right font-mono">
                    {{ s.value >= 0 ? '+' : '' }}{{ s.value.toFixed(3) }}
                  </span>
                </div>
              </div>
            </div>

            <button class="btn-secondary text-sm py-2 px-6" @click="predResult = null; predError = null">
              ← New Prediction
            </button>
          </div>

          <!-- Prediction form -->
          <form v-else @submit.prevent="runPrediction" class="space-y-5">
            <div class="grid md:grid-cols-3 gap-4">
              <div>
                <label class="form-label">Age Group</label>
                <select v-model="form.age" class="form-input">
                  <option v-for="a in ageOptions" :key="a" :value="a">{{ a }}</option>
                </select>
              </div>
              <div>
                <label class="form-label">Gender</label>
                <select v-model="form.gender" class="form-input">
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Unknown/Invalid">Unknown</option>
                </select>
              </div>
              <div>
                <label class="form-label">Race</label>
                <select v-model="form.race" class="form-input">
                  <option value="Caucasian">Caucasian</option>
                  <option value="AfricanAmerican">African American</option>
                  <option value="Hispanic">Hispanic</option>
                  <option value="Asian">Asian</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div class="grid md:grid-cols-4 gap-4">
              <div v-for="field in admissionFields" :key="field.key">
                <label class="form-label">{{ field.label }}</label>
                <input v-model.number="form[field.key]" type="number"
                  :min="field.min" :max="field.max" class="form-input" :placeholder="field.placeholder" />
              </div>
            </div>

            <div class="grid md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">HbA1c Result</label>
                <select v-model="form.A1Cresult" class="form-input">
                  <option value="None">Not Measured</option>
                  <option value=">8">&gt;8 (Uncontrolled)</option>
                  <option value=">7">&gt;7 (Borderline)</option>
                  <option value="Norm">Normal</option>
                </select>
              </div>
              <div>
                <label class="form-label">Max Glucose Serum</label>
                <select v-model="form.max_glu_serum" class="form-input">
                  <option value="None">Not Measured</option>
                  <option value=">200">&gt;200</option>
                  <option value=">300">&gt;300</option>
                  <option value="Norm">Normal</option>
                </select>
              </div>
              <div>
                <label class="form-label">Insulin</label>
                <select v-model="form.insulin" class="form-input">
                  <option value="No">No</option>
                  <option value="Steady">Steady</option>
                  <option value="Up">Up</option>
                  <option value="Down">Down</option>
                </select>
              </div>
              <div>
                <label class="form-label">Diabetes Medication</label>
                <select v-model="form.diabetesMed" class="form-input">
                  <option value="Yes">Yes</option>
                  <option value="No">No</option>
                </select>
              </div>
            </div>

            <div v-if="predError" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">
              {{ predError }}
            </div>

            <button type="submit" class="btn-primary px-8 py-2.5" :disabled="predLoading">
              <span v-if="predLoading" class="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full mr-2"></span>
              {{ predLoading ? 'Running model…' : 'Run Prediction →' }}
            </button>
          </form>
        </div>
      </div>

      <!-- Error banner -->
      <div v-if="appts.error" class="mb-4 p-4 rounded-lg bg-red-900/40 border border-red-700 text-red-300 text-sm">
        {{ appts.error }}
      </div>

      <!-- Loading -->
      <div v-if="appts.loading" class="text-center py-20 text-slate-400">Loading appointments…</div>

      <!-- Empty -->
      <div v-else-if="!appts.appointments.length" class="card text-center py-16">
        <div class="text-5xl mb-4">📅</div>
        <p class="text-slate-400">No appointments scheduled yet.</p>
        <p class="text-slate-500 text-sm mt-2">Patients will appear here once they book a session with you.</p>
      </div>

      <!-- Appointments list -->
      <div v-else class="space-y-4">
        <div
          v-for="appt in appts.appointments"
          :key="appt.id"
          class="card hover:border-navy-600 transition-colors"
        >
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <!-- Patient info -->
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-full bg-navy-700 flex items-center justify-center text-xl">
                🧑‍⚕️
              </div>
              <div>
                <div class="font-semibold text-white">{{ appt.patient_name }}</div>
                <div class="text-sm text-slate-400">{{ appt.patient_email }}</div>
              </div>
            </div>

            <!-- Date & time -->
            <div class="text-sm text-slate-300 md:text-center">
              <div class="font-medium">{{ formatDate(appt.date) }}</div>
              <div class="text-slate-400">{{ appt.time }}</div>
            </div>

            <!-- Prediction badge + status + actions -->
            <div class="flex flex-col items-start md:items-end gap-2">
              <template v-if="appt.prediction">
                <span
                  class="badge text-sm px-3 py-1"
                  :class="appt.prediction.prediction ? 'badge-red' : 'badge-green'"
                >
                  {{ appt.prediction.prediction ? '⚠ High Risk' : '✓ Low Risk' }}
                </span>
                <span class="text-xs text-slate-400 font-mono">
                  {{ (appt.prediction.probability * 100).toFixed(1) }}% readmission probability
                </span>
              </template>
              <span v-else class="badge badge-blue text-xs">No prediction on file</span>

              <!-- Appointment status badge -->
              <span
                class="badge text-xs"
                :class="{
                  'badge-blue':  appt.status === 'pending',
                  'badge-green': appt.status === 'confirmed',
                  'badge-red':   appt.status === 'cancelled',
                }"
              >
                {{ appt.status.charAt(0).toUpperCase() + appt.status.slice(1) }}
              </span>

              <!-- Confirm / Cancel buttons (only when pending) -->
              <div v-if="appt.status === 'pending'" class="flex gap-2 mt-1">
                <button
                  class="btn-primary text-xs px-3 py-1"
                  :disabled="appts.loading"
                  @click="handleStatusUpdate(appt.id, 'confirmed')"
                >
                  Confirm
                </button>
                <button
                  class="btn-secondary text-xs px-3 py-1"
                  :disabled="appts.loading"
                  @click="handleStatusUpdate(appt.id, 'cancelled')"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>

          <!-- Prediction details (expandable) -->
          <div v-if="appt.prediction?.shap_values" class="mt-5 pt-5 border-t border-navy-700">
            <button
              class="text-sm text-crimson-400 hover:text-crimson-300 font-medium flex items-center gap-1"
              @click="appt._expanded = !appt._expanded"
            >
              {{ appt._expanded ? '▾ Hide' : '▸ Show' }} prediction details
            </button>
            <div v-if="appt._expanded" class="mt-4">
              <p class="text-xs text-slate-400 mb-3">Top SHAP features for this patient:</p>
              <div class="space-y-1.5">
                <div
                  v-for="s in sortedShap(appt.prediction.shap_values).slice(0, 6)"
                  :key="s.feature"
                  class="flex items-center gap-3 text-xs"
                >
                  <span class="w-40 truncate text-slate-300 font-mono">{{ s.feature }}</span>
                  <div class="flex-1 h-2 bg-navy-700 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="s.value >= 0 ? 'bg-crimson-500' : 'bg-emerald-500'"
                      :style="{ width: Math.min(Math.abs(s.value) * 300, 100) + '%' }"
                    ></div>
                  </div>
                  <span :class="s.value >= 0 ? 'text-crimson-400' : 'text-emerald-400'" class="w-16 text-right font-mono">
                    {{ s.value >= 0 ? '+' : '' }}{{ s.value.toFixed(3) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ════════════════════════════════════════════
         PATIENT VIEW
    ════════════════════════════════════════════ -->
    <template v-else-if="auth.isPatient">
      <div class="mb-10">
        <span class="badge badge-red mb-3">Patient Portal</span>
        <h1 class="text-4xl font-display font-semibold text-white mb-2">
          Hello, {{ auth.user?.username }}
        </h1>
        <p class="text-slate-400">Run a readmission risk prediction and book an appointment with your doctor.</p>
      </div>

      <!-- Step indicator -->
      <div class="flex items-center gap-2 mb-10">
        <div v-for="(s, i) in steps" :key="s" class="flex items-center gap-2">
          <div
            class="w-7 h-7 rounded-full flex items-center justify-center text-sm font-semibold transition-colors"
            :class="step === i + 1
              ? 'bg-crimson-500 text-white'
              : step > i + 1
                ? 'bg-emerald-500 text-white'
                : 'bg-navy-700 text-slate-400'"
          >
            {{ step > i + 1 ? '✓' : i + 1 }}
          </div>
          <span class="text-sm hidden sm:block" :class="step === i + 1 ? 'text-white font-medium' : 'text-slate-500'">
            {{ s }}
          </span>
          <div v-if="i < steps.length - 1" class="w-8 h-px bg-navy-600 mx-1"></div>
        </div>
      </div>

      <!-- ── STEP 1: Prediction Form ── -->
      <div v-if="step === 1">
        <form @submit.prevent="runPrediction" class="space-y-6">
          <!-- Demographics -->
          <div class="card space-y-5">
            <h2 class="text-lg font-semibold text-white border-b border-navy-700 pb-3">Demographics</h2>
            <div class="grid md:grid-cols-3 gap-5">
              <div>
                <label class="form-label">Age Group</label>
                <select v-model="form.age" class="form-input">
                  <option v-for="a in ageOptions" :key="a" :value="a">{{ a }}</option>
                </select>
              </div>
              <div>
                <label class="form-label">Gender</label>
                <select v-model="form.gender" class="form-input">
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Unknown/Invalid">Unknown</option>
                </select>
              </div>
              <div>
                <label class="form-label">Race</label>
                <select v-model="form.race" class="form-input">
                  <option value="Caucasian">Caucasian</option>
                  <option value="AfricanAmerican">African American</option>
                  <option value="Hispanic">Hispanic</option>
                  <option value="Asian">Asian</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Admission -->
          <div class="card space-y-5">
            <h2 class="text-lg font-semibold text-white border-b border-navy-700 pb-3">Admission Details</h2>
            <div class="grid md:grid-cols-2 gap-5">
              <div v-for="field in admissionFields" :key="field.key">
                <label class="form-label">{{ field.label }}</label>
                <input v-model.number="form[field.key]" type="number"
                  :min="field.min" :max="field.max" class="form-input" :placeholder="field.placeholder" />
              </div>
            </div>
          </div>

          <!-- Lab + Medication -->
          <div class="card space-y-5">
            <h2 class="text-lg font-semibold text-white border-b border-navy-700 pb-3">Lab Results & Medications</h2>
            <div class="grid md:grid-cols-2 gap-5">
              <div>
                <label class="form-label">HbA1c Result</label>
                <select v-model="form.A1Cresult" class="form-input">
                  <option value="None">Not Measured</option>
                  <option value=">8">&gt;8 (Uncontrolled)</option>
                  <option value=">7">&gt;7 (Borderline)</option>
                  <option value="Norm">Normal</option>
                </select>
              </div>
              <div>
                <label class="form-label">Max Glucose Serum</label>
                <select v-model="form.max_glu_serum" class="form-input">
                  <option value="None">Not Measured</option>
                  <option value=">200">&gt;200</option>
                  <option value=">300">&gt;300</option>
                  <option value="Norm">Normal</option>
                </select>
              </div>
              <div>
                <label class="form-label">Diabetes Medication</label>
                <select v-model="form.diabetesMed" class="form-input">
                  <option value="Yes">Yes</option>
                  <option value="No">No</option>
                </select>
              </div>
              <div>
                <label class="form-label">Medication Change</label>
                <select v-model="form.change" class="form-input">
                  <option value="Ch">Changed</option>
                  <option value="No">No Change</option>
                </select>
              </div>
              <div>
                <label class="form-label">Insulin</label>
                <select v-model="form.insulin" class="form-input">
                  <option value="No">No</option>
                  <option value="Steady">Steady</option>
                  <option value="Up">Up</option>
                  <option value="Down">Down</option>
                </select>
              </div>
              <div>
                <label class="form-label">Metformin</label>
                <select v-model="form.metformin" class="form-input">
                  <option value="No">No</option>
                  <option value="Steady">Steady</option>
                  <option value="Up">Up</option>
                  <option value="Down">Down</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Administrative Data Flags -->
          <div class="card space-y-4">
            <h2 class="text-lg font-semibold text-white border-b border-navy-700 pb-3">Administrative Data</h2>
            <p class="text-slate-400 text-sm">Indicate which administrative records were available for this patient.</p>
            <div class="grid md:grid-cols-3 gap-4">
              <label class="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" :checked="form.has_weight === 1"
                  @change="form.has_weight = $event.target.checked ? 1 : 0"
                  class="w-4 h-4 rounded accent-sky-500" />
                <span class="text-slate-300 group-hover:text-white text-sm transition-colors">Weight recorded</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" :checked="form.has_specialty === 1"
                  @change="form.has_specialty = $event.target.checked ? 1 : 0"
                  class="w-4 h-4 rounded accent-sky-500" />
                <span class="text-slate-300 group-hover:text-white text-sm transition-colors">Medical specialty assigned</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" :checked="form.has_payer === 1"
                  @change="form.has_payer = $event.target.checked ? 1 : 0"
                  class="w-4 h-4 rounded accent-sky-500" />
                <span class="text-slate-300 group-hover:text-white text-sm transition-colors">Payer code on file</span>
              </label>
            </div>
          </div>

          <div v-if="predError" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">
            {{ predError }}
          </div>

          <button type="submit" class="btn-primary px-10 py-3" :disabled="predLoading">
            <span v-if="predLoading" class="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
            <span>{{ predLoading ? 'Running model…' : 'Run Prediction →' }}</span>
          </button>
        </form>
      </div>

      <!-- ── STEP 2: Results ── -->
      <div v-if="step === 2 && predResult">
        <div
          class="rounded-xl border p-8 mb-8 text-center"
          :class="isHighRisk ? 'bg-crimson-500/10 border-crimson-500/40' : 'bg-emerald-500/10 border-emerald-500/40'"
        >
          <div class="text-6xl font-display font-bold mb-3"
            :class="isHighRisk ? 'text-crimson-400' : 'text-emerald-400'">
            {{ (predResult.probability * 100).toFixed(1) }}%
          </div>
          <div class="text-xl font-semibold text-white mb-2">
            {{ isHighRisk ? 'High Readmission Risk' : 'Low Readmission Risk' }}
          </div>
          <p class="text-slate-400 text-sm max-w-md mx-auto">
            {{ isHighRisk
              ? 'Your data suggests an elevated risk of being readmitted within 30 days. We recommend booking an appointment.'
              : 'Your readmission risk is currently low. Continue monitoring as advised by your doctor.' }}
          </p>
          <span :class="isHighRisk ? 'badge-red' : 'badge-green'" class="badge text-sm px-4 py-1 mt-4 inline-block">
            {{ isHighRisk ? 'Readmission Predicted' : 'No Readmission Predicted' }}
          </span>
        </div>

        <!-- Top SHAP Features -->
        <div v-if="predResult.shap_values" class="card mb-8">
          <h2 class="text-lg font-semibold text-white mb-5">Top Risk Factors (SHAP)</h2>
          <div class="space-y-3">
            <div
              v-for="s in sortedShap(predResult.shap_values).slice(0, 8)"
              :key="s.feature"
              class="flex items-center gap-3 text-sm"
            >
              <span class="w-48 truncate text-slate-300 font-mono text-xs">{{ s.feature }}</span>
              <div class="flex-1 h-2.5 bg-navy-700 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :class="s.value >= 0 ? 'bg-crimson-500' : 'bg-emerald-500'"
                  :style="{ width: Math.min(Math.abs(s.value) * 300, 100) + '%' }"
                ></div>
              </div>
              <span :class="s.value >= 0 ? 'text-crimson-400' : 'text-emerald-400'" class="w-16 text-right text-xs font-mono">
                {{ s.value >= 0 ? '+' : '' }}{{ s.value.toFixed(3) }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex gap-4">
          <button class="btn-primary py-3 px-8" @click="step = 3">
            Book an Appointment →
          </button>
          <button class="btn-secondary py-3" @click="resetPrediction">
            Start Over
          </button>
        </div>
      </div>

      <!-- ── STEP 3: Book Appointment ── -->
      <div v-if="step === 3">
        <div class="mb-8">
          <h2 class="text-2xl font-display font-semibold text-white mb-2">Book an Appointment</h2>
          <p class="text-slate-400">Choose a doctor, date and time for your consultation.</p>
        </div>

        <div class="card space-y-6">
          <!-- Doctor selection -->
          <div>
            <label class="form-label">Select Doctor</label>
            <div v-if="appts.loading" class="text-slate-400 text-sm">Loading doctors…</div>
            <div v-else class="grid sm:grid-cols-2 gap-3">
              <button
                v-for="doc in appts.doctors"
                :key="doc.id"
                type="button"
                @click="booking.doctor_id = doc.id"
                class="flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-all"
                :class="booking.doctor_id === doc.id
                  ? 'border-crimson-500 bg-crimson-500/10'
                  : 'border-navy-600 bg-navy-800 hover:border-navy-500'"
              >
                <div class="w-10 h-10 rounded-full bg-navy-700 flex items-center justify-center text-xl flex-shrink-0">
                  👨‍⚕️
                </div>
                <div>
                  <div class="font-semibold text-white text-sm">{{ doc.full_name }}</div>
                  <div class="text-xs text-slate-400">{{ doc.specialty }}</div>
                </div>
              </button>
            </div>
          </div>

          <!-- Date & Time -->
          <div class="grid sm:grid-cols-2 gap-5">
            <div>
              <label class="form-label">Date</label>
              <input v-model="booking.date" type="date" class="form-input" :min="minDate" required />
            </div>
            <div>
              <label class="form-label">Time</label>
              <select v-model="booking.time" class="form-input" required>
                <option value="" disabled>Select time…</option>
                <option v-for="t in timeSlots" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
          </div>

          <div v-if="appts.error" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">
            {{ appts.error }}
          </div>

          <div class="flex gap-4">
            <button
              class="btn-primary py-3 px-8"
              :disabled="!booking.doctor_id || !booking.date || !booking.time || appts.loading"
              @click="confirmBooking"
            >
              <span v-if="appts.loading" class="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
              <span>{{ appts.loading ? 'Booking…' : 'Confirm Appointment' }}</span>
            </button>
            <button class="btn-secondary py-3" @click="step = 2">← Back</button>
          </div>
        </div>
      </div>

      <!-- ── STEP 4: Confirmation ── -->
      <div v-if="step === 4" class="text-center py-16">
        <div class="text-6xl mb-6">✅</div>
        <h2 class="text-3xl font-display font-semibold text-white mb-3">Appointment Booked!</h2>
        <p class="text-slate-400 mb-8 max-w-md mx-auto">
          Your appointment has been confirmed. The doctor will be able to see your prediction results.
        </p>
        <button class="btn-primary px-10 py-3" @click="resetAll">
          Make Another Prediction
        </button>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppointmentsStore } from '@/stores/appointments'
import api from '@/services/api'

const auth  = useAuthStore()
const appts = useAppointmentsStore()

// ── Doctor ────────────────────────────────────────────────────────────────────
const showDoctorPredForm = ref(false)

onMounted(() => {
  if (auth.isDoctor) {
    appts.fetchAppointments()
  } else if (auth.isPatient) {
    appts.fetchDoctors()
  }
})

function sortedShap(shapValues) {
  return [...shapValues].sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function handleStatusUpdate(appointmentId, newStatus) {
  try {
    await appts.updateAppointmentStatus(appointmentId, newStatus)
  } catch { /* error shown via appts.error */ }
}

// ── Patient: stepper ──────────────────────────────────────────────────────────
const steps = ['Fill Form', 'View Results', 'Book Appointment']
const step  = ref(1)

// Prediction
const predResult = ref(null)
const predLoading = ref(false)
const predError   = ref(null)
const isHighRisk  = computed(() => predResult.value?.probability > 0.5)

const defaultForm = {
  age: '[50-60)', gender: 'Female', race: 'Caucasian',
  time_in_hospital: 3, num_lab_procedures: 44, num_procedures: 1,
  num_medications: 16, number_outpatient: 0, number_inpatient: 0,
  number_emergency: 0, number_diagnoses: 9,
  A1Cresult: 'None', max_glu_serum: 'None',
  diabetesMed: 'Yes', change: 'No', insulin: 'Steady', metformin: 'No',
  has_weight: 0, has_specialty: 0, has_payer: 0
}
const form = reactive({ ...defaultForm })

const ageOptions = [
  '[0-10)', '[10-20)', '[20-30)', '[30-40)', '[40-50)',
  '[50-60)', '[60-70)', '[70-80)', '[80-90)', '[90-100)'
]

const admissionFields = [
  { key: 'time_in_hospital',   label: 'Time in Hospital (days)', min: 1,  max: 14,  placeholder: '3'  },
  { key: 'num_lab_procedures', label: 'Lab Procedures',          min: 0,  max: 132, placeholder: '44' },
  { key: 'num_procedures',     label: 'Procedures',              min: 0,  max: 6,   placeholder: '1'  },
  { key: 'num_medications',    label: 'Medications',             min: 1,  max: 81,  placeholder: '16' },
  { key: 'number_outpatient',  label: 'Outpatient Visits',       min: 0,  max: 999, placeholder: '0'  },
  { key: 'number_inpatient',   label: 'Inpatient Visits',        min: 0,  max: 999, placeholder: '0'  },
  { key: 'number_emergency',   label: 'Emergency Visits',        min: 0,  max: 999, placeholder: '0'  },
  { key: 'number_diagnoses',   label: 'Number of Diagnoses',     min: 1,  max: 16,  placeholder: '9'  }
]

async function runPrediction() {
  predLoading.value = true
  predError.value   = null
  try {
    const { data } = await api.post('/predict/', { ...form })
    predResult.value = data
    step.value = 2
  } catch (err) {
    if (!err.response) {
      predError.value = 'Network error — please check your connection and try again.'
    } else if (err.response.status === 503) {
      predError.value = 'The prediction service is temporarily unavailable. Please try again in a few moments.'
    } else if (err.response.status === 504) {
      predError.value = 'The prediction service is taking too long to respond. Please try again.'
    } else if (err.response.status === 400) {
      predError.value = err.response.data?.detail || 'Invalid input data. Please check your values and try again.'
    } else {
      predError.value = err.response?.data?.detail || 'Prediction failed. Please try again.'
    }
  } finally {
    predLoading.value = false
  }
}

// Booking
const booking = reactive({ doctor_id: null, date: '', time: '' })
const minDate = new Date().toISOString().split('T')[0]
const timeSlots = [
  '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
  '12:00', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
]

async function confirmBooking() {
  try {
    await appts.bookAppointment({
      doctor_id:     booking.doctor_id,
      date:          booking.date,
      time:          booking.time,
      prediction_id: predResult.value?.id
    })
    step.value = 4
  } catch { /* error shown above */ }
}

function resetPrediction() {
  predResult.value = null
  step.value = 1
}

function resetAll() {
  Object.assign(form, defaultForm)
  Object.assign(booking, { doctor_id: null, date: '', time: '' })
  predResult.value = null
  step.value = 1
}
</script>
