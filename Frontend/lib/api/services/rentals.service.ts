import { apiClient } from '../client'
import { RentalQuoteRequest, RentalQuoteResponse } from '../types'

export const rentalsService = {
  /**
   * Calculate authoritative rental quote from backend pricing engine.
   */
  async getQuote(payload: RentalQuoteRequest, signal?: AbortSignal): Promise<RentalQuoteResponse> {
    return apiClient<RentalQuoteResponse>('/api/v1/rentals/quote', {
      method: 'POST',
      body: JSON.stringify(payload),
      signal,
    })
  },
}
