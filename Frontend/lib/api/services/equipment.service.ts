import { apiClient } from '../client'
import { EquipmentFilterParams, EquipmentResponse, PaginatedResponse } from '../types'

export const equipmentService = {
  /**
   * Fetch equipment catalog with optional filters (featured, rentable, category, search, sorting).
   */
  async getEquipment(
    params?: EquipmentFilterParams,
    signal?: AbortSignal
  ): Promise<PaginatedResponse<EquipmentResponse>> {
    return apiClient<PaginatedResponse<EquipmentResponse>>('/api/v1/equipment', {
      params: {
        category: params?.category,
        featured: params?.featured,
        rentable: params?.rentable,
        search: params?.search,
        sort: params?.sort,
        page: params?.page ?? 1,
        limit: params?.limit ?? 50,
      },
      signal,
    })
  },

  /**
   * Fetch single equipment item by product ID slug.
   */
  async getEquipmentById(productId: string, signal?: AbortSignal): Promise<EquipmentResponse> {
    return apiClient<EquipmentResponse>(`/api/v1/equipment/${productId}`, { signal })
  },
}
