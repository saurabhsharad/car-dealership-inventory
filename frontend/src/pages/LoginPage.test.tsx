import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { login } from '../api/auth'
import { ApiError } from '../api/client'
import { AuthProvider } from '../auth/AuthProvider'
import { loadSession } from '../auth/session'
import { LoginPage } from './LoginPage'

vi.mock('../api/auth', () => ({ login: vi.fn(), register: vi.fn() }))

const loginRequest = vi.mocked(login)
const user = {
  id: 7,
  email: 'asha@example.com',
  role: 'customer' as const,
  created_at: '2026-10-23T16:40:00Z',
}

function renderLoginPage() {
  render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<p>Dashboard home</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

async function submit(email: string, password: string) {
  await userEvent.type(screen.getByLabelText('Email'), email)
  await userEvent.type(screen.getByLabelText('Password'), password)
  await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
}

beforeEach(() => {
  loginRequest.mockReset()
})

afterEach(() => {
  localStorage.clear()
})

describe('LoginPage', () => {
  it('has a labelled email field and a hidden password field', () => {
    renderLoginPage()

    expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText('Password')).toHaveAttribute(
      'type',
      'password',
    )
  })

  it('signs in and opens the dashboard', async () => {
    loginRequest.mockResolvedValue({
      access_token: 'abc.def.ghi',
      token_type: 'bearer',
      expires_in: 1800,
      user,
    })
    renderLoginPage()

    await submit('asha@example.com', 's3cure-pass')

    expect(await screen.findByText('Dashboard home')).toBeInTheDocument()
    expect(loginRequest).toHaveBeenCalledWith('asha@example.com', 's3cure-pass')
    expect(loadSession()?.user).toEqual(user)
  })

  it('shows the generic error for wrong credentials and keeps the email', async () => {
    loginRequest.mockRejectedValue(
      new ApiError(401, 'INVALID_CREDENTIALS', 'Invalid email or password.'),
    )
    renderLoginPage()

    await submit('asha@example.com', 'wrong-pass')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Invalid email or password.',
    )
    expect(screen.getByLabelText('Email')).toHaveValue('asha@example.com')
    expect(screen.queryByText('Dashboard home')).not.toBeInTheDocument()
  })

  it('says when the server cannot be reached', async () => {
    loginRequest.mockRejectedValue(
      new ApiError(0, 'NETWORK_ERROR', 'Unable to reach the server'),
    )
    renderLoginPage()

    await submit('asha@example.com', 's3cure-pass')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Unable to reach the server',
    )
  })

  it('sends only one request while signing in is in progress', async () => {
    loginRequest.mockReturnValue(new Promise(() => {}))
    renderLoginPage()

    await submit('asha@example.com', 's3cure-pass')
    const button = screen.getByRole('button', { name: 'Logging in…' })
    await userEvent.click(button)

    expect(button).toBeDisabled()
    expect(loginRequest).toHaveBeenCalledOnce()
  })

  it('links to the registration page', () => {
    renderLoginPage()

    expect(
      screen.getByRole('link', { name: 'Create an account' }),
    ).toHaveAttribute('href', '/register')
  })
})
