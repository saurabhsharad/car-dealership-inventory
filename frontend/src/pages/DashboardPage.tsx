import { useCallback, useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { listVehicles } from '../api/vehicles'
import { useAuth } from '../auth/useAuth'
import { VehicleCard } from '../components/VehicleCard'
import type { Vehicle } from '../types'

function messageFor(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Something went wrong. Please try again.'
}

export function DashboardPage() {
  const { user } = useAuth()
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      setVehicles(await listVehicles())
    } catch (error) {
      setLoadError(messageFor(error))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loading data on mount
    void load()
  }, [load])

  return (
    <>
      <h1 className="text-2xl font-semibold">Inventory</h1>
      <p className="mt-2 text-slate-600">Signed in as {user?.email}</p>

      <section aria-label="Vehicles" aria-busy={loading} className="mt-6">
        {loading && <p className="text-slate-600">Loading vehicles…</p>}
        {!loading && loadError && (
          <div
            role="alert"
            className="flex items-center gap-3 rounded-md bg-red-50 p-3 text-red-800"
          >
            <span>{loadError}</span>
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-md border border-red-300 px-3 py-1 text-sm font-medium hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600"
            >
              Retry
            </button>
          </div>
        )}
        {!loading && !loadError && vehicles.length === 0 && (
          <p className="text-slate-600">No vehicles in inventory yet</p>
        )}
        {!loading && vehicles.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {vehicles.map((vehicle) => (
              <VehicleCard key={vehicle.id} vehicle={vehicle} />
            ))}
          </div>
        )}
      </section>
    </>
  )
}
