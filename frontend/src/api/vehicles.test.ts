import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from './client'
import {
  createVehicle,
  deleteVehicle,
  listVehicles,
  purchaseVehicle,
  restockVehicle,
  searchVehicles,
  updateVehicle,
} from './vehicles'

vi.mock('./client', () => ({ apiRequest: vi.fn() }))

const request = vi.mocked(apiRequest)
const input = {
  make: 'Toyota',
  model: 'Corolla',
  category: 'Sedan',
  price: '24999.00',
}

beforeEach(() => {
  request.mockReset()
  request.mockResolvedValue([])
})

describe('vehicle API', () => {
  it('lists every vehicle', async () => {
    await listVehicles()
    expect(request).toHaveBeenCalledWith('/api/vehicles')
  })

  it('searches with only the non-empty filters', async () => {
    await searchVehicles({ make: ' toy ', model: '', min_price: '20000' })
    expect(request).toHaveBeenCalledWith(
      '/api/vehicles/search?make=toy&min_price=20000',
    )
  })

  it('creates, updates and deletes with the right method and body', async () => {
    await createVehicle({ ...input, quantity_in_stock: 3 })
    await updateVehicle(42, input)
    await deleteVehicle(42)

    expect(request).toHaveBeenNthCalledWith(1, '/api/vehicles', {
      method: 'POST',
      body: { ...input, quantity_in_stock: 3 },
    })
    expect(request).toHaveBeenNthCalledWith(2, '/api/vehicles/42', {
      method: 'PUT',
      body: input,
    })
    expect(request).toHaveBeenNthCalledWith(3, '/api/vehicles/42', {
      method: 'DELETE',
    })
  })

  it('purchases one unit and restocks a quantity', async () => {
    await purchaseVehicle(42)
    await restockVehicle(42, 5)

    expect(request).toHaveBeenNthCalledWith(1, '/api/vehicles/42/purchase', {
      method: 'POST',
    })
    expect(request).toHaveBeenNthCalledWith(2, '/api/vehicles/42/restock', {
      method: 'POST',
      body: { quantity: 5 },
    })
  })
})
