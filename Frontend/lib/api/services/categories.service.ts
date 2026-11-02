import { apiClient } from '../client'
import { CategoryResponse } from '../types'

export const categoriesService = {
  /**
   * Fetch all active categories with dynamic product counts.
   */
  async getCategories(signal?: AbortSignal): Promise<CategoryResponse[]> {
    return apiClient<CategoryResponse[]>('/api/v1/categories', { signal })
  },

  /**
   * Fetch single category by slug.
   */
  async getCategoryBySlug(slug: string, signal?: AbortSignal): Promise<CategoryResponse> {
    return apiClient<CategoryResponse>(`/api/v1/categories/${slug}`, { signal })
  },
}
