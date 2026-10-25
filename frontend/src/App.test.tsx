import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('shows the dealership shell instead of the Vite starter', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )

    const banner = screen.getByRole('banner')
    expect(banner).toHaveTextContent('Car Dealership Inventory')
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(
      screen.queryByRole('heading', { name: 'Get started' }),
    ).not.toBeInTheDocument()
  })
})
