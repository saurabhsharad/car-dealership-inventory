import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { login as loginRequest } from '../api/auth'
import { configureApiClient, type ApiError } from '../api/client'
import { AuthContext, type AuthContextValue } from './authContext'
import {
  clearSession,
  loadSession,
  saveSession,
  sessionFromLogin,
  type Session,
} from './session'

const SESSION_EXPIRED_MESSAGE = 'Your session has expired. Please log in again.'

/** Holds the session in state, mirrored to storage (SRS §8.2, A-19). */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(loadSession)
  const [notice, setNotice] = useState<string | null>(null)

  const logout = useCallback(() => {
    clearSession()
    setSession(null)
  }, [])

  // Any 401 on a request that carried our token means the session is no
  // longer valid; signing out makes the protected routes redirect to login.
  const handleUnauthorized = useCallback(
    (error: ApiError) => {
      logout()
      setNotice(error.code === 'TOKEN_EXPIRED' ? SESSION_EXPIRED_MESSAGE : null)
    },
    [logout],
  )

  // The client reads the token when each request is sent. It is configured
  // during render, not in an effect, because children's effects run before
  // this provider's and may already be loading data with a stored session.
  configureApiClient({
    getToken: () => session?.token ?? null,
    onUnauthorized: handleUnauthorized,
  })

  const login = useCallback(async (email: string, password: string) => {
    const next = sessionFromLogin(await loginRequest(email, password))
    saveSession(next)
    setSession(next)
    setNotice(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user: session?.user ?? null, notice, login, logout }),
    [session, notice, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
