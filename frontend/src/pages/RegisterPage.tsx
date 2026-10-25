import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/auth'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { TextField } from '../components/TextField'

type Field = 'email' | 'password' | 'confirmation'
type FieldErrors = Partial<Record<Field, string>>

// Mirrors the backend rules (FR-AUTH-001, FR-AUTH-003) so most mistakes are
// caught before a request is sent; the server still has the final say.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validate(
  email: string,
  password: string,
  confirmation: string,
): FieldErrors {
  const errors: FieldErrors = {}
  if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = 'Enter a valid email address.'
  }
  if (password.length < 8 || password.length > 128) {
    errors.password = 'Password must be 8 to 128 characters.'
  }
  if (confirmation !== password) {
    errors.confirmation = 'Passwords do not match.'
  }
  return errors
}

function serverFieldErrors(error: ApiError): FieldErrors {
  if (error.code === 'EMAIL_ALREADY_REGISTERED') {
    return { email: 'An account with this email already exists.' }
  }
  const errors: FieldErrors = {}
  for (const detail of error.details) {
    if (detail.field === 'email' || detail.field === 'password') {
      errors[detail.field] = detail.message
    }
  }
  return errors
}

export function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return
    const errors = validate(email, password, confirmation)
    setFieldErrors(errors)
    setFormError(null)
    if (Object.keys(errors).length > 0) return

    setSubmitting(true)
    try {
      await register(email, password)
      await login(email, password)
      navigate('/', { replace: true })
    } catch (caught) {
      if (caught instanceof ApiError) {
        const fromServer = serverFieldErrors(caught)
        if (Object.keys(fromServer).length > 0) setFieldErrors(fromServer)
        else setFormError(caught.message)
      } else {
        setFormError('Something went wrong. Please try again.')
      }
      setSubmitting(false)
    }
  }

  return (
    <section className="mx-auto max-w-sm">
      <h1 className="text-2xl font-semibold">Create an account</h1>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="mt-6 flex flex-col gap-4"
      >
        {formError && (
          <p
            role="alert"
            className="rounded-md bg-red-50 p-3 text-sm text-red-800"
          >
            {formError}
          </p>
        )}
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          error={fieldErrors.email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="new-password"
          value={password}
          error={fieldErrors.password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <TextField
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          value={confirmation}
          error={fieldErrors.confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-blue-700 px-4 py-2 font-medium text-white hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:opacity-60"
        >
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Already registered?{' '}
        <Link to="/login" className="font-medium text-blue-700 underline">
          Log in
        </Link>
      </p>
    </section>
  )
}
