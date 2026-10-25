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

/** Placeholder: writes without guarding against storage errors. */
export function saveSession(session: Session): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

/** Placeholder: trusts whatever is stored, expired or not. */
export function loadSession(now: number = Date.now()): Session | null {
  void now
  const stored = localStorage.getItem(SESSION_KEY)
  return stored === null ? null : (JSON.parse(stored) as Session)
}

export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY)
}
