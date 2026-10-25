import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import {
  createVehicle,
  deleteVehicle,
  listVehicles,
  restockVehicle,
  updateVehicle,
} from '../api/vehicles'
import { AuthProvider } from '../auth/AuthProvider'
import type { Role } from '../types'
import { signInAs, vehicle } from '../test/fixtures'
import { DashboardPage } from './DashboardPage'

vi.mock('../api/vehicles')

const list = vi.mocked(listVehicles)
const create = vi.mocked(createVehicle)
const update = vi.mocked(updateVehicle)
const remove = vi.mocked(deleteVehicle)
const restock = vi.mocked(restockVehicle)

async function renderDashboard(role: Role = 'admin', vehicles = [vehicle()]) {
  list.mockResolvedValue(vehicles)
  signInAs(role)
  render(
    <MemoryRouter>
      <AuthProvider>
        <DashboardPage />
      </AuthProvider>
    </MemoryRouter>,
  )
  await screen.findAllByRole('article')
}

function form(name: string) {
  return within(screen.getByRole('form', { name }))
}

beforeEach(() => {
  vi.resetAllMocks()
})

afterEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('controls by role', () => {
  it('shows a customer no admin controls', async () => {
    await renderDashboard('customer')

    for (const name of ['Add vehicle', 'Edit', 'Delete', 'Restock']) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument()
    }
    expect(screen.getByRole('button', { name: 'Purchase' })).toBeVisible()
  })

  it('shows an admin every control', async () => {
    await renderDashboard()

    for (const name of ['Add vehicle', 'Edit', 'Delete', 'Restock']) {
      expect(screen.getByRole('button', { name })).toBeVisible()
    }
  })
})

describe('adding a vehicle', () => {
  it('validates the fields before sending', async () => {
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Add vehicle' }))
    const add = form('Add vehicle')
    await userEvent.type(add.getByLabelText('Make'), '   ')
    await userEvent.type(add.getByLabelText('Price'), '1.999')
    await userEvent.type(add.getByLabelText('Quantity in stock'), '10001')
    await userEvent.click(add.getByRole('button', { name: 'Save' }))

    expect(add.getByLabelText('Make')).toHaveAccessibleDescription(
      'Make is required.',
    )
    expect(add.getByLabelText('Price')).toHaveAccessibleDescription(
      'Enter a price above 0 with at most 2 decimal places.',
    )
    expect(add.getByLabelText('Quantity in stock')).toHaveAccessibleDescription(
      'Enter a whole number from 0 to 10,000.',
    )
    expect(create).not.toHaveBeenCalled()
  })

  it('creates the vehicle and refreshes the list', async () => {
    create.mockResolvedValue(vehicle({ id: 2, make: 'Honda', model: 'Civic' }))
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Add vehicle' }))
    const add = form('Add vehicle')
    await userEvent.type(add.getByLabelText('Make'), ' Honda ')
    await userEvent.type(add.getByLabelText('Model'), 'Civic')
    await userEvent.type(add.getByLabelText('Category'), 'Sedan')
    await userEvent.type(add.getByLabelText('Price'), '21000.50')
    await userEvent.type(add.getByLabelText('Quantity in stock'), '4')
    list.mockResolvedValue([vehicle({ id: 2, make: 'Honda', model: 'Civic' })])
    await userEvent.click(add.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Honda Civic')).toBeInTheDocument()
    expect(create).toHaveBeenCalledWith({
      make: 'Honda',
      model: 'Civic',
      category: 'Sedan',
      price: '21000.50',
      quantity_in_stock: 4,
    })
    expect(screen.queryByRole('form', { name: 'Add vehicle' })).toBeNull()
    expect(screen.getByRole('status')).toHaveTextContent('Vehicle added.')
  })

  it('maps server validation errors to fields', async () => {
    create.mockRejectedValue(
      new ApiError(422, 'VALIDATION_ERROR', 'Request validation failed.', [
        { location: 'body', field: 'price', message: 'Price is too large' },
      ]),
    )
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Add vehicle' }))
    const add = form('Add vehicle')
    await userEvent.type(add.getByLabelText('Make'), 'Honda')
    await userEvent.type(add.getByLabelText('Model'), 'Civic')
    await userEvent.type(add.getByLabelText('Category'), 'Sedan')
    await userEvent.type(add.getByLabelText('Price'), '21000')
    await userEvent.click(add.getByRole('button', { name: 'Save' }))

    expect(await add.findByText('Price is too large')).toBeInTheDocument()
    expect(add.getByLabelText('Price')).toHaveAccessibleDescription(
      'Price is too large',
    )
  })
})

describe('editing a vehicle', () => {
  it('pre-fills the form without a stock field and saves', async () => {
    update.mockResolvedValue(vehicle({ price: '23000.00' }))
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))
    const edit = form('Edit vehicle')
    expect(edit.getByLabelText('Make')).toHaveValue('Toyota')
    expect(edit.getByLabelText('Price')).toHaveValue('24999.10')
    expect(edit.queryByLabelText('Quantity in stock')).toBeNull()

    await userEvent.clear(edit.getByLabelText('Price'))
    await userEvent.type(edit.getByLabelText('Price'), '23000')
    list.mockResolvedValue([vehicle({ price: '23000.00' })])
    await userEvent.click(edit.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('$23,000.00')).toBeInTheDocument()
    expect(update).toHaveBeenCalledWith(1, {
      make: 'Toyota',
      model: 'Corolla',
      category: 'Sedan',
      price: '23000',
    })
    expect(screen.getByRole('status')).toHaveTextContent('Vehicle updated.')
  })

  it('explains and refreshes when the vehicle is gone', async () => {
    update.mockRejectedValue(
      new ApiError(404, 'VEHICLE_NOT_FOUND', 'Vehicle not found.'),
    )
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))
    list.mockResolvedValue([])
    await userEvent.click(
      form('Edit vehicle').getByRole('button', { name: 'Save' }),
    )

    expect(
      await screen.findByText('No vehicles in inventory yet'),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      'Vehicle no longer exists',
    )
    expect(screen.queryByRole('form', { name: 'Edit vehicle' })).toBeNull()
  })
})

describe('deleting a vehicle', () => {
  it('sends nothing when the confirmation is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    await renderDashboard()

    await userEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(window.confirm).toHaveBeenCalledWith('Delete Toyota Corolla?')
    expect(remove).not.toHaveBeenCalled()
  })

  it('deletes after confirmation and refreshes the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    remove.mockResolvedValue()
    await renderDashboard()
    list.mockResolvedValue([])

    await userEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(
      await screen.findByText('No vehicles in inventory yet'),
    ).toBeInTheDocument()
    expect(remove).toHaveBeenCalledWith(1)
    expect(screen.getByRole('status')).toHaveTextContent('Vehicle deleted.')
  })
})

describe('restocking', () => {
  it('rejects a quantity outside 1 to 10,000 without a request', async () => {
    await renderDashboard()

    await userEvent.type(screen.getByLabelText('Restock quantity'), '0')
    await userEvent.click(screen.getByRole('button', { name: 'Restock' }))

    expect(
      screen.getByLabelText('Restock quantity'),
    ).toHaveAccessibleDescription('Enter a whole number from 1 to 10,000.')
    expect(restock).not.toHaveBeenCalled()
  })

  it('updates the card and re-enables Purchase', async () => {
    restock.mockResolvedValue(vehicle({ quantity_in_stock: 5 }))
    await renderDashboard('admin', [vehicle({ quantity_in_stock: 0 })])
    expect(screen.getByRole('button', { name: 'Purchase' })).toBeDisabled()

    await userEvent.type(screen.getByLabelText('Restock quantity'), '5')
    await userEvent.click(screen.getByRole('button', { name: 'Restock' }))

    expect(await screen.findByText('5 in stock')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Purchase' })).toBeEnabled()
    expect(restock).toHaveBeenCalledWith(1, 5)
    expect(screen.getByRole('status')).toHaveTextContent(
      'Restocked Toyota Corolla.',
    )
  })
})
