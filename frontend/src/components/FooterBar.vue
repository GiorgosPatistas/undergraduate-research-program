<template>
  <footer class="border-t border-navy-700 bg-navy-900 mt-auto">
    <div class="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="text-sm text-slate-500 text-center md:text-left">
        <p class="font-display font-semibold text-white mb-1">Smart Healthcare — Readmission Prediction</p>
        <p>Undergraduate Thesis · Diabetes 130-US Hospitals Dataset · XGBoost + SHAP</p>
      </div>
      <div class="flex items-center gap-6 text-xs text-slate-500">
        <RouterLink to="/" class="hover:text-slate-300 transition-colors">Home</RouterLink>
        <RouterLink to="/dashboard" class="hover:text-slate-300 transition-colors">Dashboard</RouterLink>
        <RouterLink to="/models" class="hover:text-slate-300 transition-colors">Models</RouterLink>
      </div>
    </div>
  </footer>
</template>
