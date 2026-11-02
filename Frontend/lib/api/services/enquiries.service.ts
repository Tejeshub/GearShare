import { apiClient } from '../client'
import {
  EnquirySubmissionPayload,
  EnquirySubmissionResult,
  RentalEnquiryDetail,
} from '../types'

export const enquiriesService = {
  /**
   * Submit customer rental enquiry and hold physical inventory.
   * Sends Idempotency-Key header for duplicate protection.
   */
  async submitEnquiry(
    payload: EnquirySubmissionPayload,
    idempotencyKey?: string,
    signal?: AbortSignal
  ): Promise<EnquirySubmissionResult> {
    const headers: Record<string, string> = {}
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey
    }

    return apiClient<EnquirySubmissionResult>('/api/v1/rentals/enquiries', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal,
    })
  },

  /**
   * Retrieve rental enquiry status and details by reference code.
   */
  async getEnquiryByReference(
    reference: string,
    signal?: AbortSignal
  ): Promise<RentalEnquiryDetail> {
    return apiClient<RentalEnquiryDetail>(`/api/v1/rentals/enquiries/${reference}`, {
      signal,
    })
  },
}
