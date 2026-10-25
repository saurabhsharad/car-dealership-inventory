import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { login, register } from '../api/auth'
import { ApiError } from '../api/client'
import { AuthProvider } from '../auth/AuthProvider'
import { loadSession } from '../auth/session'
import { RegisterPage } from './RegisterPage'

vi.mock('../api/auth', () => ({ login: vi.fn(), register: vi.fn() }))

const registerRequest = vi.mocked(register)
const loginRequest = vi.mocked(login)
const user = {
  id: 7,
  email: 'asha@example.com',
  role: 'customer' as const,
  created_at: '2026-10-23T16:40:00Z',
}

function renderRegisterPage() {
  render(
    <MemoryRouter initialEntries={['/register']}>
      <AuthProvider>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<p>Dashboard home</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

async function fillIn(email: string, password: string, confirmation: string) {
  await userEvent.type(screen.getByLabelText('Email'), email)
  await userEvent.type(screen.getByLabelText('Password'), password)
  await userEvent.type(screen.getByLabelText('Confirm password'), confirmation)
  await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
}

beforeEach(() => {
  registerRequest.mockReset()
  loginRequest.mockReset()
})

afterEach(() => {
  localStorage.clear()
})

describe('RegisterPage', () => {
  it('has labelled email, password and confirmation fields', () => {
    renderRegisterPage()

    expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText('Password')).toHaveAttribute(
      'type',
      'password',
    )
    expect(screen.getByLabelText('Confirm password')).toHaveAttribute(
      'type',
      'password',
    )
  })

  it('creates the account, signs in and opens the dashboard', async () => {
    registerRequest.mockResolvedValue({ user })
    loginRequest.mockResolvedValue({
      access_token: 'abc.def.ghi',
      token_type: 'bearer',
      expires_in: 1800,
      user,
    })
    renderRegisterPage()

    await fillIn('asha@example.com', 's3cure-pass', 's3cure-pass')

    expect(await screen.findByText('Dashboard home')).toBeInTheDocument()
    expect(registerRequest).toHaveBeenCalledWith(
      'asha@example.com',
      's3cure-pass',
    )
    expect(loginRequest).toHaveBeenCalledWith('asha@example.com', 's3cure-pass')
    expect(loadSession()?.user).toEqual(user)
  })

  it.each([
    [
      'mismatched passwords',
      ['asha@example.com', 's3cure-pass', 's3cure-pazz'],
      'Confirm password',
      'Passwords do not match.',
    ],
    [
      'a 7-character password',
      ['asha@example.com', 'short77', 'short77'],
      'Password',
      'Password must be 8 to 128 characters.',
    ],
    [
      'a 129-character password',
      ['asha@example.com', 'p'.repeat(129), 'p'.repeat(129)],
      'Password',
      'Password must be 8 to 128 characters.',
    ],
    [
      'an invalid email',
      ['asha@', 's3cure-pass', 's3cure-pass'],
      'Email',
      'Enter a valid email address.',
    ],
  ] as const)(
    'blocks %s without calling the API',
    async (_, [email, password, confirmation], field, message) => {
      renderRegisterPage()

      await fillIn(email, password, confirmation)

      expect(screen.getByLabelText(field)).toHaveAccessibleDescription(message)
      expect(registerRequest).not.toHaveBeenCalled()
    },
  )

  it('shows a duplicate email on the email field', async () => {
    registerRequest.mockRejectedValue(
      new ApiError(
        409,
        'EMAIL_ALREADY_REGISTERED',
        'An account with this email already exists.',
      ),
    )
    renderRegisterPage()

    await fillIn('asha@example.com', 's3cure-pass', 's3cure-pass')

    expect(
      await screen.findByText('An account with this email already exists.'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveAccessibleDescription(
      'An account with this email already exists.',
    )
    expect(loginRequest).not.toHaveBeenCalled()
    expect(screen.queryByText('Dashboard home')).not.toBeInTheDocument()
  })

  it('shows field errors the server reports', async () => {
    registerRequest.mockRejectedValue(
      new ApiError(422, 'VALIDATION_ERROR', 'Request validation failed.', [
        {
          location: 'body',
          field: 'email',
          message: 'The domain name example.invalid does not exist.',
        },
      ]),
    )
    renderRegisterPage()

    await fillIn('asha@example.invalid', 's3cure-pass', 's3cure-pass')

    expect(
      await screen.findByText(
        'The domain name example.invalid does not exist.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveAccessibleDescription(
      'The domain name example.invalid does not exist.',
    )
  })

  it('says when the server cannot be reached', async () => {
    registerRequest.mockRejectedValue(
      new ApiError(0, 'NETWORK_ERROR', 'Unable to reach the server'),
    )
    renderRegisterPage()

    await fillIn('asha@example.com', 's3cure-pass', 's3cure-pass')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Unable to reach the server',
    )
  })

  it('links to the login page', () => {
    renderRegisterPage()

    expect(screen.getByRole('link', { name: 'Log in' })).toHaveAttribute(
      'href',
      '/login',
    )
  })
})
