import { saveSession } from '../auth/session'
import type { Role, Vehicle } from '../types'

export function signInAs(role: Role = 'customer'): void {
  saveSession({
    token: 'abc.def.ghi',
    user: {
      id: 7,
      email: `${role}@example.com`,
      role,
      created_at: '2026-10-23T16:40:00Z',
    },
    expiresAt: Date.now() + 60_000,
  })
}

export function vehicle(overrides: Partial<Vehicle> = {}): Vehicle {
  return {
    id: 1,
    make: 'Toyota',
    model: 'Corolla',
    category: 'Sedan',
    price: '24999.10',
    quantity_in_stock: 3,
    created_at: '2026-10-23T16:40:00Z',
    updated_at: '2026-10-23T16:40:00Z',
    ...overrides,
  }
}
