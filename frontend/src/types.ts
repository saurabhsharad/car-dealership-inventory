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
