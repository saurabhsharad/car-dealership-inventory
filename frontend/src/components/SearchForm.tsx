import type { FormEvent } from 'react'
import type { SearchFilters } from '../types'
import { TextField } from './TextField'

export type FilterErrors = Partial<Record<keyof SearchFilters, string>>

const FIELDS: { name: keyof SearchFilters; label: string; numeric?: true }[] = [
  { name: 'make', label: 'Make' },
  { name: 'model', label: 'Model' },
  { name: 'category', label: 'Category' },
  { name: 'min_price', label: 'Min price', numeric: true },
  { name: 'max_price', label: 'Max price', numeric: true },
]

/** The search filters (FR-UI-005); the dashboard owns the values. */
export function SearchForm({
  values,
  errors,
  onChange,
  onSearch,
  onClear,
}: {
  values: SearchFilters
  errors: FilterErrors
  onChange: (values: SearchFilters) => void
  onSearch: () => void
  onClear: () => void
}) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    onSearch()
  }

  return (
    <form
      role="search"
      noValidate
      onSubmit={handleSubmit}
      className="grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-6 lg:items-end"
    >
      {FIELDS.map(({ name, label, numeric }) => (
        <TextField
          key={name}
          label={label}
          name={name}
          inputMode={numeric ? 'decimal' : undefined}
          value={values[name] ?? ''}
          error={errors[name]}
          onChange={(event) =>
            onChange({ ...values, [name]: event.target.value })
          }
        />
      ))}
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2"
        >
          Search
        </button>
        <button
          type="button"
          onClick={onClear}
          className="rounded-md border border-slate-300 px-4 py-2 font-medium hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
        >
          Clear
        </button>
      </div>
    </form>
  )
}
