<template>
  <nav class="sticky top-0 z-50 bg-navy-900/90 backdrop-blur border-b border-navy-700">
    <div class="max-w-5xl mx-auto px-6 flex items-center justify-between h-16">
      <!-- Logo -->
      <RouterLink to="/" class="flex items-center gap-2 group">
        <span class="text-crimson-500 text-2xl">🏥</span>
        <span class="font-display font-semibold text-white group-hover:text-crimson-400 transition-colors">
          SmartHealthcare
        </span>
      </RouterLink>

      <!-- Nav links (desktop) -->
      <div class="hidden md:flex items-center gap-1">
        <RouterLink
          v-for="link in navLinks"
          :key="link.name"
          :to="link.to"
          class="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-navy-700 transition-colors"
          active-class="text-white bg-navy-700"
        >
          {{ link.label }}
        </RouterLink>
      </div>

      <!-- Auth (desktop) -->
      <div class="hidden md:flex items-center gap-3">
        <template v-if="auth.isLoggedIn">
          <RouterLink to="/profile" class="flex items-center gap-2 group">
            <span
              class="badge text-xs"
              :class="auth.isDoctor ? 'badge-blue' : 'badge-red'"
            >
              {{ auth.isDoctor ? '👨‍⚕️ Doctor' : '🧑‍⚕️ Patient' }}
            </span>
            <span class="text-sm text-slate-400 group-hover:text-white transition-colors">
              {{ auth.user?.username }}
            </span>
          </RouterLink>
          <button @click="auth.logout()" class="btn-secondary text-sm py-2 px-4">
            Sign out
          </button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn-secondary text-sm py-2 px-4">Sign in</RouterLink>
          <RouterLink to="/register" class="btn-primary text-sm py-2 px-4">Register</RouterLink>
        </template>
      </div>

      <!-- Mobile menu button -->
      <button
        class="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-navy-700 transition-colors"
        @click="menuOpen = !menuOpen"
        aria-label="Toggle menu"
      >
        <svg v-if="!menuOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Mobile menu -->
    <Transition name="slide-down">
      <div v-if="menuOpen" class="md:hidden border-t border-navy-700 bg-navy-900 px-6 py-4 space-y-1">
        <RouterLink
          v-for="link in navLinks"
          :key="link.name"
          :to="link.to"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-navy-700 transition-colors"
          active-class="text-white bg-navy-700"
          @click="menuOpen = false"
        >
          {{ link.label }}
        </RouterLink>
        <div class="pt-3 border-t border-navy-700 mt-3 flex flex-col gap-2">
          <template v-if="auth.isLoggedIn">
            <RouterLink to="/profile" @click="menuOpen = false"
              class="flex items-center gap-2 px-2 pb-1 hover:opacity-80 transition-opacity">
              <span class="badge text-xs" :class="auth.isDoctor ? 'badge-blue' : 'badge-red'">
                {{ auth.isDoctor ? '👨‍⚕️ Doctor' : '🧑‍⚕️ Patient' }}
              </span>
              <span class="text-sm text-slate-300">{{ auth.user?.username }}</span>
            </RouterLink>
            <button @click="auth.logout(); menuOpen = false" class="btn-secondary w-full justify-center text-sm">
              Sign out
            </button>
          </template>
          <template v-else>
            <RouterLink to="/login" class="btn-secondary w-full justify-center text-sm" @click="menuOpen = false">
              Sign in
            </RouterLink>
            <RouterLink to="/register" class="btn-primary w-full justify-center text-sm" @click="menuOpen = false">
              Register
            </RouterLink>
          </template>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth     = useAuthStore()
const menuOpen = ref(false)

const navLinks = computed(() => {
  const base = [{ name: 'home', to: '/', label: 'Home' }]
  if (auth.isLoggedIn) {
    return [
      ...base,
      { name: 'services', to: '/services', label: 'Services' },
      { name: 'blog',     to: '/blog',     label: 'Blog'     }
    ]
  }
  return base
})
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
