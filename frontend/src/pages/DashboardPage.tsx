import { useAuth } from '../auth/useAuth'

export function DashboardPage() {
  const { user } = useAuth()
  return (
    <>
      <h1 className="text-2xl font-semibold">Inventory</h1>
      <p className="mt-2 text-slate-600">Signed in as {user?.email}</p>
    </>
  )
}
