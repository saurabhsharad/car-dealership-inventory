import type { SearchFilters, Vehicle, VehicleInput } from '../types'

const notYet = (...ignored: unknown[]): never => {
  void ignored
  throw new Error('Placeholder: vehicle API not implemented yet')
}

export const listVehicles = (): Promise<Vehicle[]> => notYet()
export const searchVehicles = (filters: SearchFilters): Promise<Vehicle[]> =>
  notYet(void filters)
export const createVehicle = (input: VehicleInput): Promise<Vehicle> =>
  notYet(void input)
export const updateVehicle = (
  id: number,
  input: VehicleInput,
): Promise<Vehicle> => notYet(void id, void input)
export const deleteVehicle = (id: number): Promise<void> => notYet(void id)
export const purchaseVehicle = (id: number): Promise<Vehicle> => notYet(void id)
export const restockVehicle = (
  id: number,
  quantity: number,
): Promise<Vehicle> => notYet(void id, void quantity)
