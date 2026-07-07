import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useBlogStore = defineStore('blog', () => {
  const articles  = ref([])
  const loading   = ref(false)
  const error     = ref(null)
  const nextPage  = ref(null)   // URL for the next page of articles
  const totalCount = ref(0)     // total number of articles from the API

  async function fetchArticles(url = '/blog/') {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.get(url)
      // Backend now returns a paginated response: { count, next, previous, results }
      articles.value = data.results
      nextPage.value  = data.next
      totalCount.value = data.count
    } catch {
      error.value = 'Could not load articles.'
    } finally {
      loading.value = false
    }
  }

  // Doctor: publish a new article
  async function publishArticle({ title, content, image_url }) {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.post('/blog/', { title, content, image_url })
      articles.value.unshift(data)
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to publish article.'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Patient: vote on an article (+1 or -1)
  // Uses POST (new vote), PATCH (change vote), or DELETE (remove vote)
  async function vote(articleId, direction) {
    const idx = articles.value.findIndex(a => a.id === articleId)
    if (idx === -1) return

    const currentVote = articles.value[idx].user_vote

    try {
      let data

      if (currentVote === null) {
        // No existing vote → POST to create
        ;({ data } = await api.post(`/blog/${articleId}/vote/`, { direction }))
      } else if (currentVote === direction) {
        // Same direction → DELETE to remove
        await api.delete(`/blog/${articleId}/vote/`)
        // Backend returns 204 No Content, so manually clear the vote locally
        articles.value[idx] = {
          ...articles.value[idx],
          user_vote: null,
          upvotes:   direction === 1  ? articles.value[idx].upvotes - 1  : articles.value[idx].upvotes,
          downvotes: direction === -1 ? articles.value[idx].downvotes - 1 : articles.value[idx].downvotes,
        }
        return
      } else {
        // Different direction → PATCH to change
        ;({ data } = await api.patch(`/blog/${articleId}/vote/`, { direction }))
      }

      articles.value[idx] = data
    } catch (err) {
      error.value = 'Could not register vote.'
    }
  }

  return { articles, loading, error, nextPage, totalCount, fetchArticles, publishArticle, vote }
})
