import { beforeEach, describe, expect, it, vi } from 'vitest'
import { login, register } from './auth'
import { apiRequest } from './client'

vi.mock('./client', () => ({ apiRequest: vi.fn() }))

const request = vi.mocked(apiRequest)
const user = {
  id: 7,
  email: 'asha@example.com',
  role: 'customer' as const,
  created_at: '2026-10-23T16:40:00Z',
}

beforeEach(() => {
  request.mockReset()
})

describe('auth API', () => {
  it('registers with POST /api/auth/register', async () => {
    request.mockResolvedValue({ user })

    const result = await register('asha@example.com', 's3cure-pass')

    expect(result).toEqual({ user })
    expect(request).toHaveBeenCalledWith('/api/auth/register', {
      method: 'POST',
      body: { email: 'asha@example.com', password: 's3cure-pass' },
    })
  })

  it('logs in with POST /api/auth/login', async () => {
    const session = {
      access_token: 'abc.def.ghi',
      token_type: 'bearer',
      expires_in: 1800,
      user,
    }
    request.mockResolvedValue(session)

    const result = await login('asha@example.com', 's3cure-pass')

    expect(result).toEqual(session)
    expect(request).toHaveBeenCalledWith('/api/auth/login', {
      method: 'POST',
      body: { email: 'asha@example.com', password: 's3cure-pass' },
    })
  })
})
