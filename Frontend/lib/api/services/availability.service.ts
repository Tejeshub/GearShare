import { apiClient } from '../client'
import {
  CombinedAvailabilityCheckRequest,
  CombinedAvailabilityCheckResponse,
  KitAvailabilityResponse,
  ProductAvailabilityResponse,
} from '../types'

export const availabilityService = {
  /**
   * Check single equipment date-wise availability.
   */
  async checkProductAvailability(
    productId: string,
    params: { startDate: string; endDate: string; quantity?: number },
    signal?: AbortSignal
  ): Promise<ProductAvailabilityResponse> {
    return apiClient<ProductAvailabilityResponse>(`/api/v1/availability/equipment/${productId}`, {
      params: {
        start_date: params.startDate,
        end_date: params.endDate,
        quantity: params.quantity ?? 1,
      },
      signal,
    })
  },

  /**
   * Check Creator Kit component availability.
   */
  async checkKitAvailability(
    kitId: string,
    params: { startDate: string; endDate: string; quantity?: number },
    signal?: AbortSignal
  ): Promise<KitAvailabilityResponse> {
    return apiClient<KitAvailabilityResponse>(`/api/v1/availability/kits/${kitId}`, {
      params: {
        start_date: params.startDate,
        end_date: params.endDate,
        quantity: params.quantity ?? 1,
      },
      signal,
    })
  },

  /**
   * Check combined equipment and kit availability for date range.
   */
  async checkCombinedAvailability(
    payload: CombinedAvailabilityCheckRequest,
    signal?: AbortSignal
  ): Promise<CombinedAvailabilityCheckResponse> {
    return apiClient<CombinedAvailabilityCheckResponse>('/api/v1/availability/check', {
      method: 'POST',
      body: JSON.stringify(payload),
      signal,
    })
  },
}
