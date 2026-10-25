import { useState, type FormEvent } from 'react'
import { TextField } from './TextField'

const WHOLE = /^\d+$/

/** Adds 1 to 10,000 units in one request (FR-INV-005). */
export function RestockControl({
  onRestock,
}: {
  onRestock: (quantity: number) => Promise<boolean>
}) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | undefined>()
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const quantity = Number(value.trim())
    if (!WHOLE.test(value.trim()) || quantity < 1 || quantity > 10_000) {
      setError('Enter a whole number from 1 to 10,000.')
      return
    }
    setError(undefined)
    setBusy(true)
    if (await onRestock(quantity)) setValue('')
    setBusy(false)
  }

  return (
    <form
      noValidate
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t border-slate-100 pt-3"
    >
      <div className="flex-1">
        <TextField
          label="Restock quantity"
          inputMode="numeric"
          value={value}
          error={error}
          onChange={(event) => setValue(event.target.value)}
        />
      </div>
      <button
        type="submit"
        disabled={busy}
        className="rounded-md border border-slate-300 px-3 py-2 font-medium hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600 disabled:opacity-60"
      >
        Restock
      </button>
    </form>
  )
}
