import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  SESSION_KEY,
  clearSession,
  loadSession,
  saveSession,
  sessionFromLogin,
  type Session,
} from './session'

const NOW = Date.UTC(2026, 9, 25, 12, 0, 0)
const user = {
  id: 7,
  email: 'asha@example.com',
  role: 'customer' as const,
  created_at: '2026-10-23T16:40:00Z',
}
const session: Session = {
  token: 'abc.def.ghi',
  user,
  expiresAt: NOW + 30 * 60 * 1000,
}

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('session storage', () => {
  it('computes the expiry from the login response', () => {
    const fromLogin = sessionFromLogin(
      {
        access_token: 'abc.def.ghi',
        token_type: 'bearer',
        expires_in: 1800,
        user,
      },
      NOW,
    )

    expect(fromLogin).toEqual(session)
  })

  it('loads back a saved session that has not expired', () => {
    saveSession(session)

    expect(loadSession(NOW)).toEqual(session)
  })

  it('has no session when nothing is stored', () => {
    expect(loadSession(NOW)).toBeNull()
  })

  it.each([
    ['has expired', 1],
    ['expires at this moment', 0],
  ])('discards a stored session that %s', (_, millisecondsLate) => {
    saveSession(session)

    expect(loadSession(session.expiresAt + millisecondsLate)).toBeNull()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it.each([
    ['is not JSON', '{not json'],
    ['has no token', JSON.stringify({ user, expiresAt: session.expiresAt })],
    [
      'has no user',
      JSON.stringify({ token: 't', expiresAt: session.expiresAt }),
    ],
    ['has no expiry', JSON.stringify({ token: 't', user })],
  ])('discards stored data that %s', (_, stored) => {
    localStorage.setItem(SESSION_KEY, stored)

    expect(loadSession(NOW)).toBeNull()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('clears the stored session', () => {
    saveSession(session)

    clearSession()

    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('keeps working when the browser refuses storage access', () => {
    const refuse = () => {
      throw new DOMException('Access denied', 'SecurityError')
    }
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(refuse)
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(refuse)
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(refuse)

    expect(() => saveSession(session)).not.toThrow()
    expect(loadSession(NOW)).toBeNull()
    expect(() => clearSession()).not.toThrow()
  })
})
