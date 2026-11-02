import { ApiError } from './errors'

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
).replace(/\/+$/, '')

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>
}

/**
 * Centralized fetch client handling serialization, error mapping, and base URL resolution.
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, headers, ...restOptions } = options

  let url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`

  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString
    }
  }

  const defaultHeaders: Record<string, string> = {
    'Accept': 'application/json',
  }

  if (restOptions.body && typeof restOptions.body === 'string') {
    defaultHeaders['Content-Type'] = 'application/json'
  }

  const mergedHeaders = {
    ...defaultHeaders,
    ...(headers as Record<string, string>),
  }

  let response: Response
  try {
    response = await fetch(url, {
      ...restOptions,
      headers: mergedHeaders,
    })
  } catch (networkError: unknown) {
    if (networkError instanceof DOMException && networkError.name === 'AbortError') {
      throw networkError
    }
    const message = networkError instanceof Error ? networkError.message : 'Network request failed'
    throw new ApiError(0, message, 'Unable to connect to the server. Please check your network connection.')
  }

  if (!response.ok) {
    let errorDetail: string | Record<string, unknown> | Array<unknown> = 'Request failed'
    try {
      const errorJson = await response.json()
      errorDetail = errorJson.detail || errorJson
    } catch {
      errorDetail = await response.text()
    }

    let userMessage = 'An unexpected error occurred.'
    if (typeof errorDetail === 'string') {
      userMessage = errorDetail
    } else if (Array.isArray(errorDetail)) {
      // Pydantic validation error list
      userMessage = errorDetail
        .map((err) => {
          if (err && typeof err === 'object' && 'msg' in err && typeof (err as { msg: unknown }).msg === 'string') {
            return (err as { msg: string }).msg
          }
          return 'Invalid field'
        })
        .join(', ')
    } else if (typeof errorDetail === 'object' && errorDetail !== null) {
      userMessage = (errorDetail as { message?: string; detail?: string }).detail ||
                    (errorDetail as { message?: string; detail?: string }).message ||
                    JSON.stringify(errorDetail)
    }

    throw new ApiError(response.status, errorDetail, userMessage)
  }

  // 204 No Content
  if (response.status === 204) {
    return {} as T
  }

  try {
    return (await response.json()) as T
  } catch {
    return {} as T
  }
}
