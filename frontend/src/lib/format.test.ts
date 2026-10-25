import { describe, expect, it } from 'vitest'
import { formatPrice } from './format'

describe('formatPrice', () => {
  it.each([
    ['24999.10', '$24,999.10'],
    ['24999.00', '$24,999.00'],
    ['0.50', '$0.50'],
    ['9999999999.99', '$9,999,999,999.99'],
  ])('shows %s as %s in US dollars', (price, shown) => {
    expect(formatPrice(price)).toBe(shown)
  })
})
