import type { ErrorDetail } from '../types'

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
  getToken: () => string | null
  onUnauthorized: (error: ApiError) => void
}

export function configureApiClient(config: ApiClientConfig): void {
  void config
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
}

/** Placeholder: a bare fetch of the path with none of the client's rules. */
export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(path, { method: options.method ?? 'GET' })
  return (await response.json()) as T
}
