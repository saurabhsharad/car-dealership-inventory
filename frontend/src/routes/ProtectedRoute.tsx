import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

/** Renders its children only for a signed-in user (FR-UI-003). */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (user === null) return <Navigate to="/login" replace />
  return children
}
