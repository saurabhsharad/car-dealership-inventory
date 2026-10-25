import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { login as loginRequest } from '../api/auth'
import { configureApiClient } from '../api/client'
import { AuthContext, type AuthContextValue } from './authContext'
import {
  clearSession,
  loadSession,
  saveSession,
  sessionFromLogin,
  type Session,
} from './session'

/** Holds the session in state, mirrored to storage (SRS §8.2, A-19). */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(loadSession)

  // The client reads the token when each request is sent. It is configured
  // during render, not in an effect, because children's effects run before
  // this provider's and may already be loading data with a stored session.
  configureApiClient({
    getToken: () => session?.token ?? null,
    onUnauthorized: () => {},
  })

  const login = useCallback(async (email: string, password: string) => {
    const next = sessionFromLogin(await loginRequest(email, password))
    saveSession(next)
    setSession(next)
  }, [])

  const logout = useCallback(() => {
    clearSession()
    setSession(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user: session?.user ?? null, login, logout }),
    [session, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
