import type { LoginResponse, RegisterResponse } from '../types'
import { apiRequest } from './client'

/** Create a customer account (FR-AUTH-001); no token is returned. */
export function register(
  email: string,
  password: string,
): Promise<RegisterResponse> {
  return apiRequest('/api/auth/register', {
    method: 'POST',
    body: { email, password },
  })
}

/** Exchange credentials for a bearer token and the user (FR-AUTH-004). */
export function login(email: string, password: string): Promise<LoginResponse> {
  return apiRequest('/api/auth/login', {
    method: 'POST',
    body: { email, password },
  })
}
