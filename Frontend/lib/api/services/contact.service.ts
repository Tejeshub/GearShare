import { apiClient } from '../client'
import { ContactMessageCreate, ContactMessageResponse } from '../types'

export const contactService = {
  /**
   * Submit a general contact enquiry message from the homepage.
   */
  async submitContactMessage(
    payload: ContactMessageCreate,
    signal?: AbortSignal
  ): Promise<ContactMessageResponse> {
    return apiClient<ContactMessageResponse>('/api/v1/contact', {
      method: 'POST',
      body: JSON.stringify(payload),
      signal,
    })
  },
}
