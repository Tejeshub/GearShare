export class ApiError extends Error {
  public status: number
  public detail: string | Record<string, unknown> | Array<unknown>
  public code?: string

  constructor(status: number, detail: string | Record<string, unknown> | Array<unknown>, message?: string) {
    const errorMsg = message || (typeof detail === 'string' ? detail : 'An unexpected API error occurred')
    super(errorMsg)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }

  get isConflict(): boolean {
    return this.status === 409
  }

  get isNotFound(): boolean {
    return this.status === 404
  }

  get isValidationError(): boolean {
    return this.status === 422
  }
}
