import { useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import type { VehicleInput } from '../types'
import { TextField } from './TextField'

type Field = 'make' | 'model' | 'category' | 'price' | 'quantity_in_stock'
type Values = Record<Field, string>
type Errors = Partial<Record<Field, string>>

const TEXT_FIELDS = [
  { name: 'make', label: 'Make' },
  { name: 'model', label: 'Model' },
  { name: 'category', label: 'Category' },
] as const

const PRICE = /^\d+(\.\d{1,2})?$/
const WHOLE = /^\d+$/
const MAX_PRICE = 9_999_999_999.99

/** The browser-side copy of FR-VEH-002; the server stays the authority. */
function validate(values: Values, withStock: boolean): Errors {
  const errors: Errors = {}
  for (const { name, label } of TEXT_FIELDS) {
    const value = values[name].trim()
    if (!value) errors[name] = `${label} is required.`
    else if (value.length > 50) {
      errors[name] = `${label} must be at most 50 characters.`
    }
  }
  const price = values.price.trim()
  if (!PRICE.test(price) || Number(price) <= 0) {
    errors.price = 'Enter a price above 0 with at most 2 decimal places.'
  } else if (Number(price) > MAX_PRICE) {
    errors.price = 'Price must be at most 9,999,999,999.99.'
  }
  const stock = values.quantity_in_stock.trim()
  if (withStock && stock && (!WHOLE.test(stock) || Number(stock) > 10_000)) {
    errors.quantity_in_stock = 'Enter a whole number from 0 to 10,000.'
  }
  return errors
}

/** Add or edit a vehicle (FR-UI-007); editing never touches stock (A-10). */
export function VehicleForm({
  title,
  initial,
  withStock,
  onSave,
  onCancel,
}: {
  title: string
  initial?: VehicleInput
  withStock: boolean
  onSave: (input: VehicleInput) => Promise<void>
  onCancel: () => void
}) {
  const [values, setValues] = useState<Values>({
    make: initial?.make ?? '',
    model: initial?.model ?? '',
    category: initial?.category ?? '',
    price: initial?.price ?? '',
    quantity_in_stock: '',
  })
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const found = validate(values, withStock)
    setErrors(found)
    setFormError(null)
    if (Object.keys(found).length > 0) return

    const input: VehicleInput = {
      make: values.make.trim(),
      model: values.model.trim(),
      category: values.category.trim(),
      price: values.price.trim(),
    }
    const stock = values.quantity_in_stock.trim()
    if (withStock && stock) input.quantity_in_stock = Number(stock)

    setSaving(true)
    try {
      await onSave(input)
    } catch (error) {
      if (error instanceof ApiError && error.status === 422) {
        const mapped: Errors = {}
        for (const detail of error.details) {
          if (detail.field) mapped[detail.field as Field] = detail.message
        }
        setErrors(mapped)
      } else {
        setFormError(
          error instanceof ApiError
            ? error.message
            : 'Something went wrong. Please try again.',
        )
      }
      setSaving(false)
    }
  }

  function field(
    name: Field,
    label: string,
    inputMode?: 'decimal' | 'numeric',
  ) {
    return (
      <TextField
        label={label}
        name={name}
        inputMode={inputMode}
        value={values[name]}
        error={errors[name]}
        onChange={(event) =>
          setValues({ ...values, [name]: event.target.value })
        }
      />
    )
  }

  return (
    <form
      aria-label={title}
      noValidate
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <h2 className="text-lg font-semibold">{title}</h2>
      {formError && (
        <p role="alert" className="rounded-md bg-red-50 p-3 text-red-800">
          {formError}
        </p>
      )}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {TEXT_FIELDS.map(({ name, label }) => (
          <div key={name}>{field(name, label)}</div>
        ))}
        {field('price', 'Price', 'decimal')}
        {withStock &&
          field('quantity_in_stock', 'Quantity in stock', 'numeric')}
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:bg-slate-300"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-slate-300 px-4 py-2 font-medium hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
