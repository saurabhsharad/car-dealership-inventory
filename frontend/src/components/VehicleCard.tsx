import type { ReactNode } from 'react'
import { formatPrice } from '../lib/format'
import type { Vehicle } from '../types'

/** One vehicle with its price and stock (FR-UI-004); actions go below. */
export function VehicleCard({
  vehicle,
  children,
}: {
  vehicle: Vehicle
  children?: ReactNode
}) {
  const soldOut = vehicle.quantity_in_stock === 0
  return (
    <article className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">
            {vehicle.make} {vehicle.model}
          </h2>
          <p className="text-sm text-slate-600">{vehicle.category}</p>
        </div>
        {soldOut && (
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">
            Out of stock
          </span>
        )}
      </div>
      <p className="text-xl font-semibold">{formatPrice(vehicle.price)}</p>
      <p className="text-sm text-slate-700">
        {vehicle.quantity_in_stock} in stock
      </p>
      {children}
    </article>
  )
}
