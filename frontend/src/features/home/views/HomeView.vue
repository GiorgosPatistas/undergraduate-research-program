<template>
  <div>

    <!-- ── Hero ─────────────────────────────────────────────────────────────── -->
    <section class="relative overflow-hidden py-24 px-6">
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute -top-40 -left-40 w-96 h-96 bg-crimson-500/10 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-crimson-600/10 rounded-full blur-3xl"></div>
      </div>

      <div class="relative max-w-4xl mx-auto text-center">
        <span class="badge badge-red text-sm mb-6">Undergraduate Thesis — 2024</span>
        <h1 class="text-5xl md:text-6xl font-display font-semibold text-white leading-tight mb-6">
          Smart Healthcare<br />
          <span class="text-crimson-400">Readmission Prediction</span>
        </h1>
        <p class="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Machine Learning system for predicting 30-day hospital readmission risk in diabetic patients.
          Built on the <strong class="text-slate-200">Diabetes 130-US Hospitals</strong> dataset
          (101,766 encounters, 1999–2008) using XGBoost with SHAP interpretability.
        </p>

        <!-- Logged-in user -->
        <div v-if="auth.isLoggedIn" class="flex flex-wrap gap-4 justify-center">
          <RouterLink to="/services" class="btn-primary text-base px-8 py-3">
            Go to Services →
          </RouterLink>
          <RouterLink to="/blog" class="btn-secondary text-base px-8 py-3">
            Read Blog
          </RouterLink>
        </div>

        <!-- Guest -->
        <div v-else class="flex flex-wrap gap-4 justify-center">
          <RouterLink to="/register" class="btn-primary text-base px-8 py-3">
            Get Started →
          </RouterLink>
          <RouterLink to="/login" class="btn-secondary text-base px-8 py-3">
            Sign In
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- ── Stats Bar ─────────────────────────────────────────────────────────── -->
    <section class="border-y border-navy-700 bg-navy-800/50 py-10 px-6">
      <div class="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
        <div v-for="stat in stats" :key="stat.label">
          <div class="text-3xl font-display font-semibold text-crimson-400 mb-1">{{ stat.value }}</div>
          <div class="text-sm text-slate-400">{{ stat.label }}</div>
        </div>
      </div>
    </section>

    <!-- ── Pages Section ─────────────────────────────────────────────────────── -->
    <section class="py-20 px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-3xl font-display font-semibold text-white text-center mb-4">Explore the Platform</h2>
        <p class="text-slate-400 text-center mb-12 max-w-xl mx-auto">
          Three dedicated spaces — each tailored to your role.
        </p>

        <div class="grid md:grid-cols-3 gap-6">

          <!-- Home card -->
          <div class="card border-navy-600 flex flex-col">
            <div class="text-4xl mb-4">🏠</div>
            <h3 class="text-xl font-display font-semibold text-white mb-2">Home</h3>
            <p class="text-slate-400 text-sm leading-relaxed flex-1">
              Overview of the project: dataset stats, ML models evaluated, and platform capabilities.
              The starting point for every visitor.
            </p>
            <div class="mt-5">
              <span class="badge badge-blue">You are here</span>
            </div>
          </div>

          <!-- Services card -->
          <div class="card hover:border-crimson-500/60 transition-colors duration-200 flex flex-col">
            <div class="text-4xl mb-4">⚕️</div>
            <h3 class="text-xl font-display font-semibold text-white mb-2">Services</h3>
            <p class="text-slate-400 text-sm leading-relaxed flex-1">
              <strong class="text-slate-200">Patients</strong> run the XGBoost readmission prediction
              and book an appointment with their chosen doctor.<br /><br />
              <strong class="text-slate-200">Doctors</strong> view their scheduled appointments and
              each patient's full prediction result with SHAP breakdown.
            </p>
            <div class="mt-5 flex gap-2 flex-wrap">
              <span class="badge badge-red text-xs">🧑‍⚕️ Patient</span>
              <span class="badge badge-blue text-xs">👨‍⚕️ Doctor</span>
            </div>
            <RouterLink
              :to="auth.isLoggedIn ? '/services' : '/login'"
              class="btn-primary mt-5 justify-center"
            >
              {{ auth.isLoggedIn ? 'Open Services →' : 'Sign in to access' }}
            </RouterLink>
          </div>

          <!-- Blog card -->
          <div class="card hover:border-crimson-500/60 transition-colors duration-200 flex flex-col">
            <div class="text-4xl mb-4">📝</div>
            <h3 class="text-xl font-display font-semibold text-white mb-2">Blog</h3>
            <p class="text-slate-400 text-sm leading-relaxed flex-1">
              <strong class="text-slate-200">Doctors</strong> publish medical articles and insights
              relevant to diabetes and readmission risk.<br /><br />
              <strong class="text-slate-200">Patients</strong> read the articles and give feedback
              through 👍 upvotes and 👎 downvotes.
            </p>
            <div class="mt-5 flex gap-2 flex-wrap">
              <span class="badge badge-blue text-xs">👨‍⚕️ Publish articles</span>
              <span class="badge badge-red text-xs">🧑‍⚕️ Vote</span>
            </div>
            <RouterLink
              :to="auth.isLoggedIn ? '/blog' : '/login'"
              class="btn-secondary mt-5 justify-center"
            >
              {{ auth.isLoggedIn ? 'Open Blog →' : 'Sign in to access' }}
            </RouterLink>
          </div>

        </div>
      </div>
    </section>

    <!-- ── How it works (Patient flow) ──────────────────────────────────────── -->
    <section class="py-16 px-6 bg-navy-800/30">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-3xl font-display font-semibold text-white text-center mb-12">How It Works</h2>
        <div class="grid md:grid-cols-2 gap-12">

          <!-- Patient flow -->
          <div>
            <div class="flex items-center gap-3 mb-6">
              <span class="badge badge-red px-3 py-1">🧑‍⚕️ Patient</span>
            </div>
            <ol class="space-y-5">
              <li v-for="(step, i) in patientSteps" :key="i" class="flex gap-4">
                <div class="w-8 h-8 rounded-full bg-crimson-500/20 border border-crimson-500/40 flex items-center justify-center text-crimson-400 font-bold text-sm flex-shrink-0 mt-0.5">
                  {{ i + 1 }}
                </div>
                <div>
                  <div class="font-semibold text-white text-sm mb-0.5">{{ step.title }}</div>
                  <div class="text-slate-400 text-sm leading-relaxed">{{ step.description }}</div>
                </div>
              </li>
            </ol>
          </div>

          <!-- Doctor flow -->
          <div>
            <div class="flex items-center gap-3 mb-6">
              <span class="badge badge-blue px-3 py-1">👨‍⚕️ Doctor</span>
            </div>
            <ol class="space-y-5">
              <li v-for="(step, i) in doctorSteps" :key="i" class="flex gap-4">
                <div class="w-8 h-8 rounded-full bg-blue-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-bold text-sm flex-shrink-0 mt-0.5">
                  {{ i + 1 }}
                </div>
                <div>
                  <div class="font-semibold text-white text-sm mb-0.5">{{ step.title }}</div>
                  <div class="text-slate-400 text-sm leading-relaxed">{{ step.description }}</div>
                </div>
              </li>
            </ol>
          </div>

        </div>
      </div>
    </section>

    <!-- ── Models ────────────────────────────────────────────────────────────── -->
    <section class="py-16 px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-3xl font-display font-semibold text-white text-center mb-12">ML Models Evaluated</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div
            v-for="model in models"
            :key="model.name"
            class="card text-center"
            :class="model.primary ? 'border-crimson-500' : ''"
          >
            <div v-if="model.primary" class="badge badge-red mx-auto mb-3">Primary</div>
            <h3 class="font-semibold text-white mb-1 text-sm">{{ model.name }}</h3>
            <div class="text-2xl font-display text-crimson-400 font-semibold">{{ model.auroc }}</div>
            <div class="text-xs text-slate-500 mt-1">AUROC</div>
          </div>
        </div>
        <p class="text-center text-slate-500 text-sm mt-6">
          All models converge near the dataset's inherent ceiling (~0.667 AUROC).
        </p>
      </div>
    </section>

    <!-- ── CTA ───────────────────────────────────────────────────────────────── -->
    <section class="py-20 px-6 text-center">
      <div class="max-w-xl mx-auto">
        <template v-if="auth.isLoggedIn">
          <h2 class="text-3xl font-display font-semibold text-white mb-4">
            Welcome back, {{ auth.user?.username }}!
          </h2>
          <p class="text-slate-400 mb-8">Head to Services to run a prediction or check the Blog for new articles.</p>
          <div class="flex gap-4 justify-center flex-wrap">
            <RouterLink to="/services" class="btn-primary text-base px-8 py-3">Services →</RouterLink>
            <RouterLink to="/blog" class="btn-secondary text-base px-8 py-3">Blog</RouterLink>
          </div>
        </template>
        <template v-else>
          <h2 class="text-3xl font-display font-semibold text-white mb-4">Ready to explore?</h2>
          <p class="text-slate-400 mb-8">Create a free account as a patient or doctor to access the full platform.</p>
          <div class="flex gap-4 justify-center flex-wrap">
            <RouterLink to="/register" class="btn-primary text-base px-8 py-3">Create Account →</RouterLink>
            <RouterLink to="/login" class="btn-secondary text-base px-8 py-3">Sign In</RouterLink>
          </div>
        </template>
      </div>
    </section>

  </div>
</template>

<script setup>
import { useAuthStore } from '@/features/account/store'

const auth = useAuthStore()

const stats = [
  { value: '101,766', label: 'Patient Encounters'         },
  { value: '4',       label: 'ML Models'                  },
  { value: '0.6716',  label: 'Best AUROC (XGBoost)'       },
  { value: '2,332',   label: 'Features After Engineering'  }
]

const patientSteps = [
  { title: 'Register as Patient',      description: 'Create an account and select the Patient role during registration.' },
  { title: 'Run a Prediction',         description: 'Fill in your clinical data in the Services page. XGBoost gives you an instant readmission risk score with SHAP explanations.' },
  { title: 'Book an Appointment',      description: 'If your risk is high, choose a doctor, pick a date and time, and confirm your appointment directly from the results screen.' },
  { title: 'Read the Blog',            description: 'Explore articles published by doctors and give feedback with 👍 / 👎 votes.' }
]

const doctorSteps = [
  { title: 'Register as Doctor',       description: 'Create an account, select Doctor, and add your full name and specialty.' },
  { title: 'View Appointments',        description: 'In Services, see all patients who have booked a session with you, along with their appointment date and time.' },
  { title: 'Review Prediction Results', description: 'Each appointment shows the patient\'s readmission probability and top SHAP features so you can prepare before the visit.' },
  { title: 'Publish Articles',         description: 'Share medical insights on the Blog. Patients can vote on your articles to show what they find most useful.' }
]

const models = [
  { name: 'XGBoost',           auroc: '0.6716', primary: true  },
  { name: 'Gradient Boosting', auroc: '0.6675', primary: false },
  { name: 'Random Forest',     auroc: '0.6625', primary: false },
  { name: 'Logistic Reg.',     auroc: '0.6231', primary: false }
]
</script>
