import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/useAuth'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ProtectedRoute } from './routes/ProtectedRoute'

function App() {
  const { user, logout } = useAuth()
  return (
    <div className="min-h-svh bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <p className="text-lg font-semibold">Car Dealership Inventory</p>
          {user && (
            <button
              type="button"
              onClick={logout}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              Log out
            </button>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
