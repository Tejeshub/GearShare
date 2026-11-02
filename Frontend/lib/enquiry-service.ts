import { enquiriesService } from './api/services/enquiries.service'
import type {
  EnquirySubmissionPayload,
  EnquirySubmissionResult,
} from './api/types'

export type { EnquirySubmissionPayload, EnquirySubmissionResult }

/**
 * Service abstraction for submitting rental enquiries.
 * Sends request to backend POST /api/v1/rentals/enquiries with Idempotency-Key.
 */
export async function submitRentalEnquiry(
  payload: EnquirySubmissionPayload,
  idempotencyKey?: string,
  signal?: AbortSignal
): Promise<EnquirySubmissionResult> {
  // Use stable idempotency key if provided or generate a client session key
  const key = idempotencyKey || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `gs-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`)
  return enquiriesService.submitEnquiry(payload, key, signal)
}
