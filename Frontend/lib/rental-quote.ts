import { calculatorProducts, finalizedProducts, creatorKits, type Product, type CreatorKit } from './products'

export interface RentalSelectionItem {
  productId: string
  quantity: number
}

export interface RentalQuoteRequest {
  productSelections: RentalSelectionItem[]
  kitId?: string | null
  startDate: string
  endDate: string
}

export interface ItemizedQuoteLine {
  id: string
  type: 'product' | 'kit'
  name: string
  brand?: string | null
  dailyRate: number
  quantity: number
  durationDays: number
  subtotal: number
}

export interface RentalQuoteResponse {
  lines: ItemizedQuoteLine[]
  durationDays: number
  subtotal: number
  discount: number
  total: number
  isProvisional: boolean
  formattedTotal: string
}

/**
 * Calculates rental duration in whole days between start and end date (inclusive).
 * Returns 0 if invalid or end is before start.
 */
export function calculateRentalDays(startDateStr: string, endDateStr: string): number {
  if (!startDateStr || !endDateStr) return 0
  const start = new Date(startDateStr)
  const end = new Date(endDateStr)
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return 0

  // Strip time components to compare calendar days accurately
  start.setHours(0, 0, 0, 0)
  end.setHours(0, 0, 0, 0)

  const diffTime = end.getTime() - start.getTime()
  if (diffTime < 0) return 0

  const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24))
  // Rental days are inclusive: start Monday and end Monday is 1 day. End Tuesday is 2 days.
  return diffDays + 1
}

/**
 * Currency formatter for Indian Rupees
 */
export function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

/**
 * Pure business logic for estimating rental costs.
 * Deduplicates individual items already included in a selected Creator Kit.
 */
export function calculateRentalQuote(request: RentalQuoteRequest): RentalQuoteResponse {
  const { productSelections, kitId, startDate, endDate } = request
  const durationDays = calculateRentalDays(startDate, endDate)

  const lines: ItemizedQuoteLine[] = []

  let kit: CreatorKit | undefined = undefined
  if (kitId) {
    kit = creatorKits.find((k) => k.id === kitId)
  }

  // 1. Add Kit line if selected
  if (kit && durationDays > 0) {
    lines.push({
      id: kit.id,
      type: 'kit',
      name: kit.title,
      dailyRate: kit.price,
      quantity: 1,
      durationDays,
      subtotal: kit.price * 1 * durationDays,
    })
  }

  // Set of product IDs already included in the kit (to avoid duplicate individual charging)
  const kitProductIds = new Set(kit ? kit.productIds : [])

  // 2. Add individual products
  for (const sel of productSelections) {
    if (sel.quantity <= 0) continue

    // If already covered by the kit, avoid double-charging unless user requested extra quantity
    if (kitProductIds.has(sel.productId)) {
      // already included in base kit
      continue
    }

    const product =
      calculatorProducts.find((p) => p.id === sel.productId) ||
      finalizedProducts.find((p) => p.id === sel.productId)

    if (product && durationDays > 0) {
      lines.push({
        id: product.id,
        type: 'product',
        name: product.name,
        brand: product.brand,
        dailyRate: product.price,
        quantity: sel.quantity,
        durationDays,
        subtotal: product.price * sel.quantity * durationDays,
      })
    }
  }

  const subtotal = lines.reduce((acc, line) => acc + line.subtotal, 0)
  const discount = 0 // Transparent pricing: no arbitrary hidden discounts unless configured
  const total = Math.max(0, subtotal - discount)

  return {
    lines,
    durationDays,
    subtotal,
    discount,
    total,
    isProvisional: true,
    formattedTotal: formatINR(total),
  }
}
