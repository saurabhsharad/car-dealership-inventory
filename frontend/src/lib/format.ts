const usd = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

/** The one place prices are formatted, in US dollars (A-15). */
export function formatPrice(price: string): string {
  return usd.format(Number(price))
}
