// Shapes of the API's JSON, mirroring SRS §4.3.

export type Role = 'customer' | 'admin'

export interface PublicUser {
  id: number
  email: string
  role: Role
  created_at: string
}

export interface RegisterResponse {
  user: PublicUser
}

export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: PublicUser
}

/** One entry of a 422 response's details (SRS §4.2). */
export interface ErrorDetail {
  location: string
  field: string | null
  message: string
}

export interface Vehicle {
  id: number
  make: string
  model: string
  category: string
  /** Two-decimal string such as "24999.00", never a float (SRS §4.1). */
  price: string
  quantity_in_stock: number
  created_at: string
  updated_at: string
}

export interface VehicleInput {
  make: string
  model: string
  category: string
  price: string
  quantity_in_stock?: number
}

export interface SearchFilters {
  make?: string
  model?: string
  category?: string
  min_price?: string
  max_price?: string
}
