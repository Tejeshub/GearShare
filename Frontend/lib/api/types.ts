/**
 * Type definitions matching FastAPI Pydantic v2 schemas.
 * Field names are camelCase matching FastAPI alias_generator=to_camel.
 */

// -------------------------------------------------------------
// Category
// -------------------------------------------------------------
export interface CategoryResponse {
  id: string
  name: string
  slug: string
  description?: string | null
  isActive: boolean
  isVisibleInCategorySection: boolean
  sortOrder: number
  productCount: number
  createdAt: string
  updatedAt: string
}

// -------------------------------------------------------------
// Equipment
// -------------------------------------------------------------
export type AvailabilityStatus = 'Available' | 'Low Stock' | 'Reserved'

export interface EquipmentResponse {
  id: string
  dbId: string
  name: string
  brand: string
  category: string
  categorySlug: string
  description: string
  image: string
  spec: string
  specs: string[]
  price: number
  availability: AvailabilityStatus
  isFeatured: boolean
  isRentable: boolean
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface EquipmentFilterParams {
  category?: string
  featured?: boolean
  rentable?: boolean
  search?: string
  sort?: string
  page?: number
  limit?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

// -------------------------------------------------------------
// Creator Kits
// -------------------------------------------------------------
export interface CreatorKitItemResponse {
  id: string
  role: string
  name: string
  quantity: number
  sortOrder: number
  productId?: string | null
}

export interface CreatorKitResponse {
  id: string
  title: string
  tag: string
  intendedUse: string
  description: string
  image: string
  price: number
  isActive: boolean
  sortOrder: number
  includedItems: CreatorKitItemResponse[]
  productIds: string[]
  createdAt: string
  updatedAt: string
}

// -------------------------------------------------------------
// Rental Quote & Pricing
// -------------------------------------------------------------
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

export interface BundledItemInfo {
  role: string
  name: string
  quantity: number
  productId?: string | null
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
  bundledItems?: BundledItemInfo[] | null
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

// -------------------------------------------------------------
// Date-wise Availability
// -------------------------------------------------------------
export interface ProductAvailabilityResponse {
  productId: string
  productName: string
  startDate: string
  endDate: string
  totalActiveUnits: number
  availableQuantity: number
  requestedQuantity: number
  isAvailable: boolean
  availableAssetCodes?: string[] | null
}

export interface KitComponentAvailability {
  role: string
  name: string
  productId?: string | null
  isCatalogueLinked: boolean
  requiredQuantity: number
  availableQuantity?: number | null
  isAvailable: boolean
  reason?: string | null
}

export interface KitAvailabilityResponse {
  kitId: string
  kitTitle: string
  startDate: string
  endDate: string
  requestedQuantity: number
  isAvailable: boolean
  components: KitComponentAvailability[]
}

export interface ProductAvailabilityReport {
  productId: string
  productName: string
  requestedQuantity: number
  availableQuantity: number
  isAvailable: boolean
  reason?: string | null
}

export interface CombinedAvailabilityCheckRequest {
  productSelections: RentalSelectionItem[]
  kitId?: string | null
  startDate: string
  endDate: string
}

export interface CombinedAvailabilityCheckResponse {
  startDate: string
  endDate: string
  isAvailable: boolean
  products: ProductAvailabilityReport[]
  kit?: KitAvailabilityResponse | null
}

// -------------------------------------------------------------
// Rental Enquiry & Reservation
// -------------------------------------------------------------
export type EnquiryStatus =
  | 'Pending Review'
  | 'Confirmed'
  | 'Rejected'
  | 'Expired'
  | 'Cancelled'
  | 'Completed'

export interface EnquirySubmissionPayload {
  customerName: string
  email: string
  phone: string
  message?: string | null
  productSelections: RentalSelectionItem[]
  kitId?: string | null
  startDate: string
  endDate: string
  durationDays?: number
  calculatedEstimate?: number
}

export interface EnquirySubmissionResult {
  success: boolean
  referenceId: string
  isSimulated: boolean
  message: string
  status: EnquiryStatus
  holdExpiresAt: string
  quote: RentalQuoteResponse
  confirmationEmailSent?: boolean
}

export interface EnquiryItemDetail {
  id: string
  itemType: string
  name: string
  brand?: string | null
  dailyRate: number
  quantity: number
  durationDays: number
  subtotal: number
  bundledComponents?: Array<Record<string, unknown>> | null
}

export interface RentalEnquiryDetail {
  id: string
  reference: string
  customerName: string
  email: string
  phone: string
  message?: string | null
  startDate: string
  endDate: string
  durationDays: number
  subtotal: number
  discount: number
  estimatedTotal: number
  status: EnquiryStatus
  holdExpiresAt: string
  createdAt: string
  updatedAt: string
  items: EnquiryItemDetail[]
}

// -------------------------------------------------------------
// Contact Messages
// -------------------------------------------------------------
export interface ContactMessageCreate {
  name: string
  email: string
  message: string
}

export interface ContactMessageResponse {
  id: string
  name: string
  email: string
  message: string
  createdAt: string
}
