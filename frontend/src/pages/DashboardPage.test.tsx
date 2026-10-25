import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { listVehicles } from '../api/vehicles'
import { ApiError } from '../api/client'
import { AuthProvider } from '../auth/AuthProvider'
import { signInAs, vehicle } from '../test/fixtures'
import { DashboardPage } from './DashboardPage'

vi.mock('../api/vehicles')

const list = vi.mocked(listVehicles)

function renderDashboard() {
  signInAs('customer')
  render(
    <MemoryRouter>
      <AuthProvider>
        <DashboardPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.mocked(listVehicles).mockReset()
})

afterEach(() => {
  localStorage.clear()
})

describe('DashboardPage', () => {
  it('shows a busy region while vehicles load', () => {
    list.mockReturnValue(new Promise(() => {}))
    renderDashboard()

    expect(screen.getByText('Loading vehicles…')).toBeInTheDocument()
    expect(screen.getByLabelText('Vehicles')).toHaveAttribute(
      'aria-busy',
      'true',
    )
  })

  it('says when there are no vehicles yet', async () => {
    list.mockResolvedValue([])
    renderDashboard()

    expect(
      await screen.findByText('No vehicles in inventory yet'),
    ).toBeInTheDocument()
  })

  it('shows a card per vehicle with price, stock and a sold-out badge', async () => {
    list.mockResolvedValue([
      vehicle({ id: 1 }),
      vehicle({ id: 2, model: 'Camry', quantity_in_stock: 0 }),
    ])
    renderDashboard()

    const cards = await screen.findAllByRole('article')
    expect(cards).toHaveLength(2)
    const corolla = within(cards[0])
    expect(corolla.getByRole('heading')).toHaveTextContent('Toyota Corolla')
    expect(corolla.getByText('Sedan')).toBeInTheDocument()
    expect(corolla.getByText('$24,999.10')).toBeInTheDocument()
    expect(corolla.getByText('3 in stock')).toBeInTheDocument()
    expect(corolla.queryByText('Out of stock')).not.toBeInTheDocument()
    expect(within(cards[1]).getByText('Out of stock')).toBeInTheDocument()
  })

  it('shows a failed load with a Retry that tries again', async () => {
    list
      .mockRejectedValueOnce(
        new ApiError(0, 'NETWORK_ERROR', 'Unable to reach the server'),
      )
      .mockResolvedValueOnce([vehicle()])
    renderDashboard()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Unable to reach the server',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByRole('article')).toBeInTheDocument()
    expect(list).toHaveBeenCalledTimes(2)
  })
})
