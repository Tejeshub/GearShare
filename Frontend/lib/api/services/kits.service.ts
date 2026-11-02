import { apiClient } from '../client'
import { CreatorKitResponse } from '../types'

export const kitsService = {
  /**
   * Fetch all active Creator Kits with authoritative bundled item relationships.
   */
  async getKits(signal?: AbortSignal): Promise<CreatorKitResponse[]> {
    return apiClient<CreatorKitResponse[]>('/api/v1/kits', { signal })
  },

  /**
   * Fetch single Creator Kit by ID slug.
   */
  async getKitById(kitId: string, signal?: AbortSignal): Promise<CreatorKitResponse> {
    return apiClient<CreatorKitResponse>(`/api/v1/kits/${kitId}`, { signal })
  },
}
