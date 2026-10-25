import { createContext } from 'react'
import type { PublicUser } from '../types'

export interface AuthContextValue {
  user: PublicUser | null
  /** Why the user was signed out, to show on the login page, if any. */
  notice: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
