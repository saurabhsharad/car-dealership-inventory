import { useCallback, useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import {
  createVehicle,
  deleteVehicle,
  listVehicles,
  purchaseVehicle,
  restockVehicle,
  searchVehicles,
  updateVehicle,
} from '../api/vehicles'
import { useAuth } from '../auth/useAuth'
import { RestockControl } from '../components/RestockControl'
import { SearchForm, type FilterErrors } from '../components/SearchForm'
import { VehicleCard } from '../components/VehicleCard'
import { VehicleForm } from '../components/VehicleForm'
import type { SearchFilters, Vehicle, VehicleInput } from '../types'

function messageFor(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Something went wrong. Please try again.'
}

function hasFilters(filters: SearchFilters): boolean {
  return Object.values(filters).some((value) => value?.trim())
}

/** Checks the browser can make before searching (A-16). */
function checkFilters(filters: SearchFilters): FilterErrors {
  const min = filters.min_price?.trim()
  const max = filters.max_price?.trim()
  if (min && max && Number(min) > Number(max)) {
    return { max_price: 'Max price must be at least the min price.' }
  }
  return {}
}

/** Field errors from a 422, keyed by the query parameter they name. */
function fieldErrorsFrom(error: ApiError): FilterErrors {
  const errors: FilterErrors = {}
  for (const detail of error.details ?? []) {
    if (detail.field) {
      errors[detail.field as keyof SearchFilters] = detail.message
    }
  }
  return errors
}

export function DashboardPage() {
  const { user } = useAuth()
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [filters, setFilters] = useState<SearchFilters>({})
  const [applied, setApplied] = useState<SearchFilters>({})
  const [filterErrors, setFilterErrors] = useState<FilterErrors>({})
  const [status, setStatus] = useState('')
  const [purchasingId, setPurchasingId] = useState<number | null>(null)
  const [editing, setEditing] = useState<Vehicle | 'new' | null>(null)
  const isAdmin = user?.role === 'admin'

  const load = useCallback(async (query: SearchFilters) => {
    setLoading(true)
    setLoadError(null)
    try {
      setVehicles(
        hasFilters(query) ? await searchVehicles(query) : await listVehicles(),
      )
      setApplied(query)
    } catch (error) {
      if (error instanceof ApiError && error.status === 422) {
        setFilterErrors(fieldErrorsFrom(error))
      } else {
        setLoadError(messageFor(error))
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loading data on mount
    void load({})
  }, [load])

  function search() {
    const errors = checkFilters(filters)
    setFilterErrors(errors)
    if (Object.keys(errors).length === 0) void load(filters)
  }

  function clear() {
    setFilters({})
    setFilterErrors({})
    void load({})
  }

  function replace(id: number, change: (vehicle: Vehicle) => Vehicle) {
    setVehicles((current) =>
      current.map((vehicle) => (vehicle.id === id ? change(vehicle) : vehicle)),
    )
  }

  async function purchase(vehicle: Vehicle) {
    setPurchasingId(vehicle.id)
    setStatus('')
    try {
      const updated = await purchaseVehicle(vehicle.id)
      replace(vehicle.id, () => updated)
      setStatus(`Purchased ${vehicle.make} ${vehicle.model}.`)
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        replace(vehicle.id, (current) => ({ ...current, quantity_in_stock: 0 }))
        setStatus('This vehicle just sold out.')
      } else if (error instanceof ApiError && error.status === 404) {
        setStatus('This vehicle is no longer available')
        void load(applied)
      } else {
        setStatus(messageFor(error))
      }
    } finally {
      setPurchasingId(null)
    }
  }

  /** A vehicle deleted elsewhere: say so and show the current list. */
  function handleGone() {
    setStatus('Vehicle no longer exists')
    void load(applied)
  }

  async function save(input: VehicleInput) {
    if (editing === 'new') {
      await createVehicle(input)
      setStatus('Vehicle added.')
    } else if (editing) {
      try {
        await updateVehicle(editing.id, input)
        setStatus('Vehicle updated.')
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 404)) throw error
        setEditing(null)
        handleGone()
        return
      }
    }
    setEditing(null)
    void load(applied)
  }

  async function remove(vehicle: Vehicle) {
    if (!window.confirm(`Delete ${vehicle.make} ${vehicle.model}?`)) return
    setStatus('')
    try {
      await deleteVehicle(vehicle.id)
      setStatus('Vehicle deleted.')
      void load(applied)
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) handleGone()
      else setStatus(messageFor(error))
    }
  }

  async function restock(vehicle: Vehicle, quantity: number) {
    setStatus('')
    try {
      const updated = await restockVehicle(vehicle.id, quantity)
      replace(vehicle.id, () => updated)
      setStatus(`Restocked ${vehicle.make} ${vehicle.model}.`)
      return true
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) handleGone()
      else setStatus(messageFor(error))
      return false
    }
  }

  const filtered = hasFilters(applied)

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Inventory</h1>
          <p className="mt-2 text-slate-600">Signed in as {user?.email}</p>
        </div>
        {isAdmin && (
          <button
            type="button"
            onClick={() => setEditing('new')}
            className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2"
          >
            Add vehicle
          </button>
        )}
      </div>

      {isAdmin && editing && (
        <div className="mt-6">
          <VehicleForm
            key={editing === 'new' ? 'new' : editing.id}
            title={editing === 'new' ? 'Add vehicle' : 'Edit vehicle'}
            initial={editing === 'new' ? undefined : editing}
            withStock={editing === 'new'}
            onSave={save}
            onCancel={() => setEditing(null)}
          />
        </div>
      )}

      <div className="mt-6">
        <SearchForm
          values={filters}
          errors={filterErrors}
          onChange={setFilters}
          onSearch={search}
          onClear={clear}
        />
      </div>

      <p role="status" aria-live="polite" className="mt-4 min-h-6 text-sm">
        {status}
      </p>

      <section aria-label="Vehicles" aria-busy={loading} className="mt-2">
        {loading && <p className="text-slate-600">Loading vehicles…</p>}
        {!loading && loadError && (
          <div
            role="alert"
            className="flex items-center gap-3 rounded-md bg-red-50 p-3 text-red-800"
          >
            <span>{loadError}</span>
            <button
              type="button"
              onClick={() => void load(applied)}
              className="rounded-md border border-red-300 px-3 py-1 text-sm font-medium hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600"
            >
              Retry
            </button>
          </div>
        )}
        {!loading && !loadError && vehicles.length === 0 && !filtered && (
          <p className="text-slate-600">No vehicles in inventory yet</p>
        )}
        {!loading && !loadError && vehicles.length === 0 && filtered && (
          <div className="flex items-center gap-3 text-slate-600">
            <span>No vehicles match your filters</span>
            <button
              type="button"
              onClick={clear}
              className="rounded-md border border-slate-300 px-3 py-1 text-sm font-medium hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              Clear
            </button>
          </div>
        )}
        {!loading && vehicles.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {vehicles.map((vehicle) => {
              const pending = purchasingId === vehicle.id
              return (
                <VehicleCard key={vehicle.id} vehicle={vehicle}>
                  <button
                    type="button"
                    disabled={vehicle.quantity_in_stock === 0 || pending}
                    onClick={() => void purchase(vehicle)}
                    className="mt-auto rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600"
                  >
                    {pending ? 'Purchasing…' : 'Purchase'}
                  </button>
                  {isAdmin && (
                    <>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setEditing(vehicle)}
                          className="flex-1 rounded-md border border-slate-300 px-3 py-2 font-medium hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => void remove(vehicle)}
                          className="flex-1 rounded-md border border-red-300 px-3 py-2 font-medium text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-600"
                        >
                          Delete
                        </button>
                      </div>
                      <RestockControl
                        onRestock={(quantity) => restock(vehicle, quantity)}
                      />
                    </>
                  )}
                </VehicleCard>
              )
            })}
          </div>
        )}
      </section>
    </>
  )
}
