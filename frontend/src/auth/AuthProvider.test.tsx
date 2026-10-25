import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { login } from '../api/auth'
import {
  ApiError,
  configureApiClient,
  type ApiClientConfig,
} from '../api/client'
import { AuthProvider } from './AuthProvider'
import { useAuth } from './useAuth'
import { SESSION_KEY, loadSession, saveSession } from './session'

vi.mock('../api/auth', () => ({ login: vi.fn(), register: vi.fn() }))
vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/client')>()),
  configureApiClient: vi.fn(),
}))

const loginRequest = vi.mocked(login)
const user = {
  id: 7,
  email: 'asha@example.com',
  role: 'customer' as const,
  created_at: '2026-10-23T16:40:00Z',
}
const loginResponse = {
  access_token: 'abc.def.ghi',
  token_type: 'bearer' as const,
  expires_in: 1800,
  user,
}

/** A minimal consumer that shows the auth state and offers its actions. */
function Probe() {
  const { user, login, logout } = useAuth()
  return (
    <>
      <p>{user ? `Signed in as ${user.email}` : 'Signed out'}</p>
      <button
        onClick={() => login('asha@example.com', 's3cure-pass').catch(() => {})}
      >
        Log in
      </button>
      <button onClick={logout}>Log out</button>
    </>
  )
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

function clientConfig(): ApiClientConfig {
  const calls = vi.mocked(configureApiClient).mock.calls
  return calls[calls.length - 1][0]
}

beforeEach(() => {
  localStorage.clear()
  loginRequest.mockReset()
  vi.mocked(configureApiClient).mockClear()
})

afterEach(() => {
  localStorage.clear()
})

describe('AuthProvider', () => {
  it('starts signed out when nothing is stored', () => {
    renderWithAuth()

    expect(screen.getByText('Signed out')).toBeInTheDocument()
  })

  it('starts signed in from a valid stored session', () => {
    saveSession({ token: 'abc.def.ghi', user, expiresAt: Date.now() + 60_000 })

    renderWithAuth()

    expect(
      screen.getByText('Signed in as asha@example.com'),
    ).toBeInTheDocument()
  })

  it('logs in through the API and stores the session', async () => {
    loginRequest.mockResolvedValue(loginResponse)
    renderWithAuth()

    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))

    expect(
      await screen.findByText('Signed in as asha@example.com'),
    ).toBeInTheDocument()
    expect(loginRequest).toHaveBeenCalledWith('asha@example.com', 's3cure-pass')
    expect(loadSession()).toMatchObject({ token: 'abc.def.ghi', user })
  })

  it('stays signed out and stores nothing when login fails', async () => {
    loginRequest.mockRejectedValue(
      new ApiError(401, 'INVALID_CREDENTIALS', 'Invalid email or password.'),
    )
    renderWithAuth()

    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))

    expect(screen.getByText('Signed out')).toBeInTheDocument()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('logs out by clearing the user and the stored session', async () => {
    saveSession({ token: 'abc.def.ghi', user, expiresAt: Date.now() + 60_000 })
    renderWithAuth()

    await userEvent.click(screen.getByRole('button', { name: 'Log out' }))

    expect(screen.getByText('Signed out')).toBeInTheDocument()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('gives the API client the current token, including on first render', async () => {
    saveSession({ token: 'stored.token', user, expiresAt: Date.now() + 60_000 })
    renderWithAuth()

    expect(configureApiClient).toHaveBeenCalled()
    expect(clientConfig().getToken()).toBe('stored.token')

    await userEvent.click(screen.getByRole('button', { name: 'Log out' }))
    expect(clientConfig().getToken()).toBeNull()

    loginRequest.mockResolvedValue(loginResponse)
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    await screen.findByText('Signed in as asha@example.com')
    expect(clientConfig().getToken()).toBe('abc.def.ghi')
  })
})
