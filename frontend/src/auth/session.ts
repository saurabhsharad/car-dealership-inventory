import type { LoginResponse, PublicUser } from '../types'

/** A logged-in session as the browser keeps it (SRS §8.2, A-19). */
export interface Session {
  token: string
  user: PublicUser
  /** When the token expires, in milliseconds since the epoch. */
  expiresAt: number
}

export const SESSION_KEY = 'dealership.session'

export function sessionFromLogin(
  response: LoginResponse,
  now: number = Date.now(),
): Session {
  return {
    token: response.access_token,
    user: response.user,
    expiresAt: now + response.expires_in * 1000,
  }
}

// Storage can throw (private browsing, blocked site data), so every access
// is guarded: the app then simply behaves as if nothing were stored.

export function saveSession(session: Session): void {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  } catch {
    // The session still lives in memory for this tab.
  }
}

/** The stored session, or null if absent, unreadable or expired (FR-UI-003). */
export function loadSession(now: number = Date.now()): Session | null {
  let stored: string | null
  try {
    stored = localStorage.getItem(SESSION_KEY)
  } catch {
    return null
  }
  if (stored === null) return null

  const session = parseSession(stored)
  if (session === null || session.expiresAt <= now) {
    clearSession()
    return null
  }
  return session
}

export function clearSession(): void {
  try {
    localStorage.removeItem(SESSION_KEY)
  } catch {
    // Nothing more can be done; an unreadable session is never loaded.
  }
}

function parseSession(stored: string): Session | null {
  try {
    const value: unknown = JSON.parse(stored)
    if (
      typeof value === 'object' &&
      value !== null &&
      'token' in value &&
      typeof value.token === 'string' &&
      'user' in value &&
      typeof value.user === 'object' &&
      value.user !== null &&
      'expiresAt' in value &&
      typeof value.expiresAt === 'number'
    ) {
      return value as Session
    }
  } catch {
    // Not JSON.
  }
  return null
}
