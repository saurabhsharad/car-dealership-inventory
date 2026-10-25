import type { ErrorDetail } from '../types'

/** An error response from the API, or a failure to reach it. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: ErrorDetail[]

  constructor(
    status: number,
    code: string,
    message: string,
    details: ErrorDetail[] = [],
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export interface ApiClientConfig {
  /** The current access token, or null when logged out. */
  getToken: () => string | null
  /** Called when a request that carried a token gets a 401. */
  onUnauthorized: (error: ApiError) => void
}

let config: ApiClientConfig = {
  getToken: () => null,
  onUnauthorized: () => {},
}

export function configureApiClient(next: ApiClientConfig): void {
  config = next
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
}

/** Send a JSON request to the API; resolve with its JSON or throw ApiError. */
export async function apiRequest<T>(
  path: string,
  { method = 'GET', body }: RequestOptions = {},
): Promise<T> {
  const token = config.getToken()
  const headers = new Headers({ Accept: 'application/json' })
  if (body !== undefined) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL ?? ''}${path}`,
      {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      },
    )
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Unable to reach the server')
  }

  if (response.ok) {
    return (response.status === 204 ? undefined : await response.json()) as T
  }

  const error = await toApiError(response)
  if (response.status === 401 && token) config.onUnauthorized(error)
  throw error
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const { error } = await response.json()
    if (typeof error?.code === 'string' && typeof error?.message === 'string') {
      return new ApiError(
        response.status,
        error.code,
        error.message,
        Array.isArray(error.details) ? error.details : [],
      )
    }
  } catch {
    // Not JSON: fall through to the generic error below.
  }
  return new ApiError(
    response.status,
    'HTTP_ERROR',
    'Something went wrong. Please try again.',
  )
}
