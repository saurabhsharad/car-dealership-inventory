import { useContext } from 'react'
import { AuthContext, type AuthContextValue } from './authContext'

/** The signed-in user and the login and logout actions. */
export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (value === null) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return value
}
