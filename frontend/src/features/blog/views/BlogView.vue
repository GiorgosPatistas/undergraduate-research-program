<template>
  <div class="max-w-4xl mx-auto px-6 py-12">

    <!-- Header -->
    <div class="flex items-start justify-between mb-10 gap-4 flex-wrap">
      <div>
        <h1 class="text-4xl font-display font-semibold text-white mb-2">Blog</h1>
        <p class="text-slate-400">
          {{ auth.isDoctor
            ? 'Share medical insights and articles with patients.'
            : 'Read articles from our doctors and share your feedback.' }}
        </p>
      </div>
      <!-- Doctor: publish button -->
      <button v-if="auth.isDoctor" class="btn-primary py-2.5" @click="showForm = !showForm">
        {{ showForm ? '✕ Cancel' : '+ New Article' }}
      </button>
    </div>

    <!-- ── Doctor: publish form ── -->
    <div v-if="auth.isDoctor && showForm" class="card mb-8">
      <h2 class="text-lg font-semibold text-white mb-5">Publish New Article</h2>
      <form @submit.prevent="handlePublish" class="space-y-5">
        <div>
          <label class="form-label">Title</label>
          <input v-model="newArticle.title" type="text" class="form-input"
            placeholder="e.g. Understanding HbA1c Levels in Diabetic Patients" required />
        </div>
        <div>
          <label class="form-label">Content</label>
          <textarea
            v-model="newArticle.content"
            class="form-input resize-none"
            rows="6"
            placeholder="Write your article here…"
            required
          ></textarea>
        </div>
        <div>
          <label class="form-label">Cover Image URL <span class="text-slate-500">(optional)</span></label>
          <input v-model="newArticle.image_url" type="url" class="form-input"
            placeholder="https://example.com/image.jpg" />
        </div>

        <div v-if="blog.error" class="rounded-lg bg-crimson-500/10 border border-crimson-500/30 px-4 py-3 text-crimson-300 text-sm">
          {{ blog.error }}
        </div>

        <div class="flex gap-3">
          <button type="submit" class="btn-primary py-2.5" :disabled="blog.loading">
            <span v-if="blog.loading" class="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
            {{ blog.loading ? 'Publishing…' : 'Publish Article' }}
          </button>
          <button type="button" class="btn-secondary py-2.5" @click="showForm = false">Cancel</button>
        </div>
      </form>
    </div>

    <!-- Loading -->
    <div v-if="blog.loading && !blog.articles.length" class="text-center py-20 text-slate-400">
      Loading articles…
    </div>

    <!-- Empty -->
    <div v-else-if="!blog.articles.length" class="card text-center py-16">
      <div class="text-5xl mb-4">📝</div>
      <p class="text-slate-400">No articles published yet.</p>
      <p v-if="auth.isDoctor" class="text-slate-500 text-sm mt-2">
        Be the first to share an article with patients.
      </p>
    </div>

    <!-- Articles list -->
    <div v-else class="space-y-6">
      <article
        v-for="article in blog.articles"
        :key="article.id"
        class="card hover:border-navy-600 transition-colors"
      >
        <!-- Cover image -->
        <img
          v-if="article.image_url"
          :src="article.image_url"
          :alt="article.title"
          class="w-full h-44 object-cover rounded-lg mb-5 bg-navy-700"
          @error="(e) => e.target.style.display = 'none'"
        />

        <!-- Meta -->
        <div class="flex items-center gap-3 mb-3">
          <div class="w-8 h-8 rounded-full bg-navy-700 flex items-center justify-center text-sm">
            👨‍⚕️
          </div>
          <div>
            <span class="text-sm font-medium text-white">{{ article.author_name }}</span>
            <span class="text-slate-500 text-xs ml-2">{{ formatDate(article.created_at) }}</span>
          </div>
          <span class="badge badge-blue ml-auto">Medical</span>
        </div>

        <!-- Title -->
        <h2 class="text-xl font-display font-semibold text-white mb-3">{{ article.title }}</h2>

        <!-- Content preview -->
        <p class="text-slate-400 text-sm leading-relaxed mb-5">
          {{ article.content.length > 280 ? article.content.slice(0, 280) + '…' : article.content }}
        </p>

        <!-- Read more toggle -->
        <button
          v-if="article.content.length > 280"
          class="text-crimson-400 hover:text-crimson-300 text-sm font-medium mb-5"
          @click="article._expanded = !article._expanded"
        >
          {{ article._expanded ? 'Show less ▲' : 'Read more ▼' }}
        </button>
        <p v-if="article._expanded" class="text-slate-400 text-sm leading-relaxed mb-5">
          {{ article.content }}
        </p>

        <!-- Divider -->
        <div class="border-t border-navy-700 pt-4 flex items-center gap-4">
          <!-- Patient: vote buttons -->
          <template v-if="auth.isPatient">
            <div class="flex items-center gap-3">
              <button
                @click="handleVote(article.id, 1)"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                :class="article.user_vote === 1
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-navy-700 text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10'"
              >
                👍 {{ article.upvotes || 0 }}
              </button>
              <button
                @click="handleVote(article.id, -1)"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                :class="article.user_vote === -1
                  ? 'bg-crimson-500/20 text-crimson-300 border border-crimson-500/40'
                  : 'bg-navy-700 text-slate-400 hover:text-crimson-400 hover:bg-crimson-500/10'"
              >
                👎 {{ article.downvotes || 0 }}
              </button>
            </div>
            <span class="text-slate-500 text-xs ml-2">
              {{ totalVotes(article) }} vote{{ totalVotes(article) !== 1 ? 's' : '' }}
            </span>
          </template>

          <!-- Doctor: see vote stats -->
          <template v-else>
            <span class="text-sm text-slate-400">
              👍 {{ article.upvotes || 0 }} &nbsp;·&nbsp; 👎 {{ article.downvotes || 0 }}
            </span>
          </template>
        </div>
      </article>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/features/account/store'
import { useBlogStore } from '@/features/blog/store'

const auth = useAuthStore()
const blog = useBlogStore()

const showForm = ref(false)
const newArticle = reactive({ title: '', content: '', image_url: '' })

onMounted(() => blog.fetchArticles())

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function totalVotes(article) {
  return (article.upvotes || 0) + (article.downvotes || 0)
}

async function handlePublish() {
  try {
    await blog.publishArticle({ ...newArticle })
    newArticle.title     = ''
    newArticle.content   = ''
    newArticle.image_url = ''
    showForm.value = false
  } catch { /* error shown above */ }
}

async function handleVote(articleId, direction) {
  await blog.vote(articleId, direction)
}
</script>
