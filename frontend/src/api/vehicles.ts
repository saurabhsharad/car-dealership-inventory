import type { SearchFilters, Vehicle, VehicleInput } from '../types'
import { apiRequest } from './client'

export function listVehicles(): Promise<Vehicle[]> {
  return apiRequest('/api/vehicles')
}

/** Search with only the filters that have a value (FR-UI-005). */
export function searchVehicles(filters: SearchFilters): Promise<Vehicle[]> {
  const query = new URLSearchParams()
  for (const [name, value] of Object.entries(filters)) {
    const trimmed = value?.trim()
    if (trimmed) query.set(name, trimmed)
  }
  return apiRequest(`/api/vehicles/search?${query}`)
}

export function createVehicle(input: VehicleInput): Promise<Vehicle> {
  return apiRequest('/api/vehicles', { method: 'POST', body: input })
}

export function updateVehicle(
  id: number,
  input: VehicleInput,
): Promise<Vehicle> {
  return apiRequest(`/api/vehicles/${id}`, { method: 'PUT', body: input })
}

export function deleteVehicle(id: number): Promise<void> {
  return apiRequest(`/api/vehicles/${id}`, { method: 'DELETE' })
}

export function purchaseVehicle(id: number): Promise<Vehicle> {
  return apiRequest(`/api/vehicles/${id}/purchase`, { method: 'POST' })
}

export function restockVehicle(id: number, quantity: number): Promise<Vehicle> {
  return apiRequest(`/api/vehicles/${id}/restock`, {
    method: 'POST',
    body: { quantity },
  })
}
