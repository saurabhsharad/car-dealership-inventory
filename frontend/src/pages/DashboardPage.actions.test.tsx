import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import { listVehicles, purchaseVehicle, searchVehicles } from '../api/vehicles'
import { AuthProvider } from '../auth/AuthProvider'
import { signInAs, vehicle } from '../test/fixtures'
import { DashboardPage } from './DashboardPage'

vi.mock('../api/vehicles')

const list = vi.mocked(listVehicles)
const purchase = vi.mocked(purchaseVehicle)
const search = vi.mocked(searchVehicles)

async function renderDashboard(vehicles = [vehicle()]) {
  list.mockResolvedValue(vehicles)
  signInAs('customer')
  render(
    <MemoryRouter>
      <AuthProvider>
        <DashboardPage />
      </AuthProvider>
    </MemoryRouter>,
  )
  await screen.findAllByRole('article')
}

beforeEach(() => {
  vi.resetAllMocks()
})

afterEach(() => {
  localStorage.clear()
})

describe('purchasing', () => {
  it('disables Purchase at zero stock', async () => {
    await renderDashboard([vehicle({ quantity_in_stock: 0 })])

    expect(screen.getByRole('button', { name: 'Purchase' })).toBeDisabled()
  })

  it('buys one unit, updates the card and confirms', async () => {
    purchase.mockResolvedValue(vehicle({ quantity_in_stock: 2 }))
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Purchase' }))

    expect(await screen.findByText('2 in stock')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      'Purchased Toyota Corolla.',
    )
    expect(purchase).toHaveBeenCalledOnce()
    expect(purchase).toHaveBeenCalledWith(1)
  })

  it('sends one request while a purchase is pending', async () => {
    purchase.mockReturnValue(new Promise(() => {}))
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Purchase' }))
    const busy = screen.getByRole('button', { name: 'Purchasing…' })
    await userEvent.click(busy)

    expect(busy).toBeDisabled()
    expect(purchase).toHaveBeenCalledOnce()
  })

  it('marks the card sold out when someone else bought the last unit', async () => {
    purchase.mockRejectedValue(
      new ApiError(409, 'OUT_OF_STOCK', 'This vehicle is out of stock.'),
    )
    await renderDashboard([vehicle({ quantity_in_stock: 1 })])

    await userEvent.click(screen.getByRole('button', { name: 'Purchase' }))

    expect(await screen.findByText('Out of stock')).toBeInTheDocument()
    expect(screen.getByText('0 in stock')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      'This vehicle just sold out.',
    )
  })

  it('reloads the list when the vehicle no longer exists', async () => {
    purchase.mockRejectedValue(
      new ApiError(404, 'VEHICLE_NOT_FOUND', 'Vehicle not found.'),
    )
    await renderDashboard()
    list.mockResolvedValue([])

    await userEvent.click(screen.getByRole('button', { name: 'Purchase' }))

    expect(
      await screen.findByText('No vehicles in inventory yet'),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      'This vehicle is no longer available',
    )
    expect(list).toHaveBeenCalledTimes(2)
  })
})

describe('searching', () => {
  it('searches with the filters given and shows the matches', async () => {
    search.mockResolvedValue([vehicle({ id: 9, model: 'Camry' })])
    await renderDashboard()

    await userEvent.type(screen.getByLabelText('Make'), 'toy')
    await userEvent.type(screen.getByLabelText('Min price'), '20000')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))

    expect(await screen.findByText('Toyota Camry')).toBeInTheDocument()
    expect(search).toHaveBeenCalledWith(
      expect.objectContaining({ make: 'toy', min_price: '20000' }),
    )
  })

  it('uses the list when no filter is set', async () => {
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Search' }))

    expect(search).not.toHaveBeenCalled()
    expect(list).toHaveBeenCalledTimes(2)
  })

  it('blocks a minimum above the maximum without a request', async () => {
    await renderDashboard()

    await userEvent.type(screen.getByLabelText('Min price'), '500')
    await userEvent.type(screen.getByLabelText('Max price'), '100')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))

    expect(screen.getByLabelText('Max price')).toHaveAccessibleDescription(
      'Max price must be at least the min price.',
    )
    expect(search).not.toHaveBeenCalled()
  })

  it('shows server field errors from the search', async () => {
    search.mockRejectedValue(
      new ApiError(422, 'VALIDATION_ERROR', 'Request validation failed.', [
        { location: 'query', field: 'min_price', message: 'Too many decimals' },
      ]),
    )
    await renderDashboard()

    await userEvent.type(screen.getByLabelText('Min price'), '1.999')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))

    expect(await screen.findByText('Too many decimals')).toBeInTheDocument()
    expect(screen.getByLabelText('Min price')).toHaveAccessibleDescription(
      'Too many decimals',
    )
  })

  it('offers Clear when nothing matches, which reloads the list', async () => {
    search.mockResolvedValue([])
    await renderDashboard()

    await userEvent.type(screen.getByLabelText('Make'), 'ferrari')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(
      await screen.findByText('No vehicles match your filters'),
    ).toBeInTheDocument()

    await userEvent.click(screen.getAllByRole('button', { name: 'Clear' })[0])

    expect(await screen.findByText('Toyota Corolla')).toBeInTheDocument()
    expect(screen.getByLabelText('Make')).toHaveValue('')
  })
})
