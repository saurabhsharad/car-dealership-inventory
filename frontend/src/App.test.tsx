import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import App from './App'
import { AuthProvider } from './auth/AuthProvider'
import { saveSession } from './auth/session'

function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  )
}

function signIn() {
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
}

afterEach(() => {
  localStorage.clear()
})

describe('App', () => {
  it('shows the dealership shell instead of the Vite starter', () => {
    renderApp()

    const banner = screen.getByRole('banner')
    expect(banner).toHaveTextContent('Car Dealership Inventory')
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(
      screen.queryByRole('heading', { name: 'Get started' }),
    ).not.toBeInTheDocument()
  })

  it('sends a signed-out visitor from the dashboard to the login page', () => {
    renderApp('/')

    expect(screen.getByRole('heading', { name: 'Log in' })).toBeInTheDocument()
    expect(
      screen.queryByRole('heading', { name: 'Inventory' }),
    ).not.toBeInTheDocument()
  })

  it('shows the dashboard to a signed-in user', () => {
    signIn()

    renderApp('/')

    expect(
      screen.getByRole('heading', { name: 'Inventory' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Signed in as asha@example.com'),
    ).toBeInTheDocument()
  })

  it('serves the public register page', () => {
    renderApp('/register')
    expect(
      screen.getByRole('heading', { name: 'Create an account' }),
    ).toBeInTheDocument()
  })

  it('sends an unknown path to the dashboard route', () => {
    signIn()

    renderApp('/no-such-page')

    expect(
      screen.getByRole('heading', { name: 'Inventory' }),
    ).toBeInTheDocument()
  })
})
