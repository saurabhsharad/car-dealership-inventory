import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest, configureApiClient } from './client'

const BASE_URL = 'http://api.test'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function errorResponse(status: number, code: string, message: string) {
  return jsonResponse(status, { error: { code, message } })
}

const fetchMock = vi.fn<typeof fetch>()
const onUnauthorized = vi.fn<(error: ApiError) => void>()
let token: string | null = null

function sentRequest(): { url: string; init: RequestInit } {
  const [url, init] = fetchMock.mock.calls[0]
  return { url: String(url), init: init ?? {} }
}

function sentHeaders(): Headers {
  return new Headers(sentRequest().init.headers)
}

async function caught(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (error) {
    if (error instanceof ApiError) return error
    throw error
  }
  throw new Error('expected the request to fail')
}

beforeEach(() => {
  vi.stubEnv('VITE_API_BASE_URL', BASE_URL)
  vi.stubGlobal('fetch', fetchMock)
  token = null
  configureApiClient({ getToken: () => token, onUnauthorized })
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  fetchMock.mockReset()
  onUnauthorized.mockReset()
})

describe('apiRequest', () => {
  it('calls the configured base URL and returns the parsed JSON', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, [{ id: 1 }]))

    const result = await apiRequest<{ id: number }[]>('/api/vehicles')

    expect(result).toEqual([{ id: 1 }])
    expect(sentRequest().url).toBe('http://api.test/api/vehicles')
    expect(sentRequest().init.method).toBe('GET')
    expect(sentHeaders().get('Accept')).toBe('application/json')
  })

  it('sends a body as JSON', async () => {
    fetchMock.mockResolvedValue(jsonResponse(201, { user: { id: 1 } }))

    await apiRequest('/api/auth/register', {
      method: 'POST',
      body: { email: 'a@x.com', password: 's3cure-pass' },
    })

    expect(sentRequest().init.method).toBe('POST')
    expect(sentHeaders().get('Content-Type')).toBe('application/json')
    expect(JSON.parse(String(sentRequest().init.body))).toEqual({
      email: 'a@x.com',
      password: 's3cure-pass',
    })
  })

  it('adds the bearer token only when there is one', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, []))

    await apiRequest('/api/vehicles')
    expect(sentHeaders().has('Authorization')).toBe(false)

    fetchMock.mockClear()
    fetchMock.mockResolvedValue(jsonResponse(200, []))
    token = 'abc.def.ghi'
    await apiRequest('/api/vehicles')
    expect(sentHeaders().get('Authorization')).toBe('Bearer abc.def.ghi')
  })

  it('returns undefined for 204 No Content', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(
      apiRequest('/api/vehicles/1', { method: 'DELETE' }),
    ).resolves.toBeUndefined()
  })

  it('turns the error envelope into an ApiError with field details', async () => {
    const details = [{ location: 'body', field: 'price', message: 'too low' }]
    fetchMock.mockResolvedValue(
      jsonResponse(422, {
        error: { code: 'VALIDATION_ERROR', message: 'Invalid.', details },
      }),
    )

    const error = await caught(apiRequest('/api/vehicles', { method: 'POST' }))

    expect(error).toMatchObject({
      status: 422,
      code: 'VALIDATION_ERROR',
      message: 'Invalid.',
      details,
    })
  })

  it('reports a body that is not the envelope as a generic error', async () => {
    fetchMock.mockResolvedValue(
      new Response('<html>Bad Gateway</html>', { status: 502 }),
    )

    const error = await caught(apiRequest('/api/vehicles'))

    expect(error).toMatchObject({
      status: 502,
      code: 'HTTP_ERROR',
      message: 'Something went wrong. Please try again.',
      details: [],
    })
  })

  it('reports a network failure as "Unable to reach the server"', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    const error = await caught(apiRequest('/api/vehicles'))

    expect(error).toMatchObject({
      status: 0,
      code: 'NETWORK_ERROR',
      message: 'Unable to reach the server',
    })
  })

  it('calls the unauthorized handler for a 401 on a request with a token', async () => {
    token = 'expired.token'
    fetchMock.mockResolvedValue(
      errorResponse(401, 'TOKEN_EXPIRED', 'Your session has expired.'),
    )

    const error = await caught(apiRequest('/api/vehicles'))

    expect(error.code).toBe('TOKEN_EXPIRED')
    expect(onUnauthorized).toHaveBeenCalledOnce()
    expect(onUnauthorized).toHaveBeenCalledWith(error)
  })

  it('does not call the handler for a 401 without a token, such as a bad login', async () => {
    fetchMock.mockResolvedValue(
      errorResponse(401, 'INVALID_CREDENTIALS', 'Invalid email or password.'),
    )

    const error = await caught(
      apiRequest('/api/auth/login', { method: 'POST', body: {} }),
    )

    expect(error.code).toBe('INVALID_CREDENTIALS')
    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})
