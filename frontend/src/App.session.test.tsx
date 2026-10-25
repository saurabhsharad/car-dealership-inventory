import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { apiRequest } from './api/client'
import { AuthProvider } from './auth/AuthProvider'
import { SESSION_KEY, saveSession } from './auth/session'

const fetchMock = vi.fn<typeof fetch>()

function renderSignedIn() {
  saveSession({
    token: 'abc.def.ghi',
    user: {
      id: 7,
      email: 'asha@example.com',
      role: 'customer',
      created_at: '2026-10-23T16:40:00Z',
    },
    expiresAt: Date.now() + 60_000,
  })
  render(
    <MemoryRouter initialEntries={['/']}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  )
}

function respondWith401(code: string, message: string) {
  fetchMock.mockResolvedValue(
    new Response(JSON.stringify({ error: { code, message } }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}

async function requestSomethingProtected() {
  await act(async () => {
    await apiRequest('/api/vehicles').catch(() => {})
  })
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  fetchMock.mockReset()
  localStorage.clear()
})

describe('session handling', () => {
  it('logs out from the header and returns to the login page', async () => {
    renderSignedIn()

    await userEvent.click(screen.getByRole('button', { name: 'Log out' }))

    expect(screen.getByRole('heading', { name: 'Log in' })).toBeInTheDocument()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
    expect(
      screen.queryByRole('button', { name: 'Log out' }),
    ).not.toBeInTheDocument()
  })

  it('sends the user to login with a message when the token has expired', async () => {
    renderSignedIn()
    respondWith401('TOKEN_EXPIRED', 'Your session has expired.')

    await requestSomethingProtected()

    expect(screen.getByRole('heading', { name: 'Log in' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      'Your session has expired. Please log in again.',
    )
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('signs out on any other 401 without the expiry message', async () => {
    renderSignedIn()
    respondWith401('NOT_AUTHENTICATED', 'Authentication required.')

    await requestSomethingProtected()

    expect(screen.getByRole('heading', { name: 'Log in' })).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })
})
