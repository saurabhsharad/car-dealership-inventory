import type { ReactNode } from 'react'
import { AuthContext, type AuthContextValue } from './authContext'

/** Placeholder: always signed out; login and logout do nothing. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const value: AuthContextValue = {
    user: null,
    login: async () => {},
    logout: () => {},
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
