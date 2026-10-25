import type { LoginResponse, RegisterResponse } from '../types'

export async function register(
  email: string,
  password: string,
): Promise<RegisterResponse> {
  void email
  void password
  throw new Error('Placeholder: register is not implemented yet')
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  void email
  void password
  throw new Error('Placeholder: login is not implemented yet')
}
