import { createContext } from 'react'
import type { PublicUser } from '../types'

export interface AuthContextValue {
  user: PublicUser | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
