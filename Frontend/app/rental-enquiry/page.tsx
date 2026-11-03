'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Suspense, useMemo, useState, useEffect } from 'react'
import {
  calculatorProducts,
  finalizedProducts,
  creatorKits,
  type Product,
  type CreatorKit,
} from '@/lib/products'
import {
  calculateRentalQuote,
  calculateRentalDays,
  formatINR,
  type RentalQuoteResponse,
} from '@/lib/rental-quote'
import {
  submitRentalEnquiry,
  type EnquirySubmissionPayload,
  type EnquirySubmissionResult,
} from '@/lib/enquiry-service'
import {
  equipmentService,
  kitsService,
  rentalsService,
  availabilityService,
  type EquipmentResponse,
  type CreatorKitResponse,
  type CombinedAvailabilityCheckResponse,
} from '@/lib/api'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Plus,
  Trash2,
  Calendar,
  AlertCircle,
  ShieldCheck,
  Sparkles,
  ChevronDown,
  Clock,
} from 'lucide-react'
import { SiteNav } from '@/components/SiteNav'

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-4 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#82868a]">
      {children}
    </p>
  )
}

function RentalEnquiryContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Retrieve initial params
  const kitParam = searchParams.get('kit')
  const productParam = searchParams.get('product')
  const qtyParam = searchParams.get('qty')
  const itemsParam = searchParams.get('items')
  const startDateParam = searchParams.get('startDate')
  const endDateParam = searchParams.get('endDate')
  const originParam = searchParams.get('origin')

  // Dynamic back to previous browsing location
  const backHref = useMemo(() => {
    if (originParam === 'kits') return '/#kits'
    if (originParam === 'calculator') return '/#calculator'
    if (originParam === 'gear') return '/#gear'
    return '/#gear'
  }, [originParam])

  // Dynamic catalog from backend
  const [backendEquipment, setBackendEquipment] = useState<EquipmentResponse[]>([])
  const [backendKits, setBackendKits] = useState<CreatorKitResponse[]>([])
  const [serverQuote, setServerQuote] = useState<RentalQuoteResponse | null>(null)
  const [isQuoteLoading, setIsQuoteLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [availabilityWarning, setAvailabilityWarning] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    equipmentService
      .getEquipment({ limit: 100 })
      .then((res) => {
        if (active && res.items.length > 0) setBackendEquipment(res.items)
      })
      .catch((err) => console.error('Failed to load equipment list:', err))

    kitsService
      .getKits()
      .then((data) => {
        if (active && data.length > 0) setBackendKits(data)
      })
      .catch((err) => console.error('Failed to load kits list:', err))

    return () => {
      active = false
    }
  }, [])

  // Available catalog list for adding more items (authoritative backend + fallback)
  const allAvailableProducts = useMemo(() => {
    if (backendEquipment.length > 0) {
      return backendEquipment
    }
    const map = new Map<string, Product>()
    calculatorProducts.forEach((p) => map.set(p.id, p))
    finalizedProducts.forEach((p) => map.set(p.id, p))
    return Array.from(map.values())
  }, [backendEquipment])

  const allAvailableKits = useMemo(() => {
    return backendKits.length > 0 ? backendKits : creatorKits
  }, [backendKits])

  // State: Selected Creator Kit ID
  const [selectedKitId, setSelectedKitId] = useState<string | null>(() => {
    if (kitParam && (creatorKits.some((k) => k.id === kitParam) || true)) {
      return kitParam
    }
    return null
  })

  // State: Selected Product Quantities (map: productId -> quantity)
  const [productQuantities, setProductQuantities] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {}

    // Check multiple items parameter (e.g., "sony-fx30:1,sony-24-70-gm2:2")
    if (itemsParam) {
      const pairs = itemsParam.split(',')
      for (const pair of pairs) {
        const [id, qStr] = pair.split(':')
        const q = parseInt(qStr || '1', 10)
        if (id && q > 0) initial[id] = q
      }
    }

    // Check single product parameter
    if (productParam && !initial[productParam]) {
      const q = parseInt(qtyParam || '1', 10)
      initial[productParam] = q > 0 ? q : 1
    }

    return initial
  })

  // State: Dates
  const minDate = useMemo(() => new Date().toISOString().split('T')[0], [])

  const [startDate, setStartDate] = useState<string>(() => {
    if (startDateParam) return startDateParam
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split('T')[0]
  })

  const [endDate, setEndDate] = useState<string>(() => {
    if (endDateParam) return endDateParam
    const d = new Date()
    d.setDate(d.getDate() + 4)
    return d.toISOString().split('T')[0]
  })

  // State: Customer Details
  const [customerName, setCustomerName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [message, setMessage] = useState('')

  // State: UI & Submission
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submissionResult, setSubmissionResult] = useState<EnquirySubmissionResult | null>(null)
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() =>
    typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `gs-${Date.now()}`
  )
  const [mobileSummaryOpen, setMobileSummaryOpen] = useState(false)
  const [showAddDrawer, setShowAddDrawer] = useState(false)

  // Creator Kit details & bundled items deduplication
  const selectedKit: CreatorKit | CreatorKitResponse | null = useMemo(() => {
    if (!selectedKitId) return null
    return allAvailableKits.find((k) => k.id === selectedKitId) || null
  }, [selectedKitId, allAvailableKits])

  const kitBundledProductIds = useMemo(() => {
    return new Set(selectedKit ? selectedKit.productIds : [])
  }, [selectedKit])

  // Pure Calculation & Quote
  const rentalDays = useMemo(() => calculateRentalDays(startDate, endDate), [startDate, endDate])

  const productSelections = useMemo(() => {
    return Object.entries(productQuantities).map(([productId, quantity]) => ({
      productId,
      quantity,
    }))
  }, [productQuantities])

  const localQuote: RentalQuoteResponse = useMemo(() => {
    return calculateRentalQuote({
      productSelections,
      kitId: selectedKitId,
      startDate,
      endDate,
    })
  }, [productSelections, selectedKitId, startDate, endDate])

  // Debounced server quote and availability check
  useEffect(() => {
    if (rentalDays <= 0 || (productSelections.length === 0 && !selectedKitId)) {
      setServerQuote(null)
      setAvailabilityWarning(null)
      return
    }

    const abortController = new AbortController()
    setIsQuoteLoading(true)

    const timer = setTimeout(() => {
      rentalsService
        .getQuote(
          {
            productSelections,
            kitId: selectedKitId,
            startDate,
            endDate,
          },
          abortController.signal
        )
        .then((q) => {
          setServerQuote(q)
          setIsQuoteLoading(false)
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return
          setServerQuote(null)
          setIsQuoteLoading(false)
          const errorMsg = err instanceof Error ? err.message : 'Unable to calculate quote for selected items'
          setAvailabilityWarning(`Quote Notice: ${errorMsg}`)
        })

      availabilityService
        .checkCombinedAvailability(
          {
            productSelections,
            kitId: selectedKitId,
            startDate,
            endDate,
          },
          abortController.signal
        )
        .then((res) => {
          if (!res.isAvailable) {
            const unavail = res.products.filter((p) => !p.isAvailable).map((p) => p.productName).join(', ')
            const kitMsg = res.kit && !res.kit.isAvailable ? `${res.kit.kitTitle} components` : ''
            setAvailabilityWarning(
              `Some requested items are currently unavailable for these dates: ${[unavail, kitMsg].filter(Boolean).join('; ')}`
            )
          } else {
            setAvailabilityWarning(null)
          }
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return
          console.error('Availability check failed:', err)
        })
    }, 250)

    return () => {
      clearTimeout(timer)
      abortController.abort()
    }
  }, [productSelections, selectedKitId, startDate, endDate, rentalDays])

  const quote = serverQuote || localQuote

  // List of selected product objects
  const selectedProductsList = useMemo(() => {
    return Object.entries(productQuantities)
      .filter(([, q]) => q > 0)
      .map(([id, quantity]) => {
        const product = allAvailableProducts.find((p) => p.id === id)
        return { product, quantity }
      })
      .filter((item): item is { product: Product | EquipmentResponse; quantity: number } => item.product !== undefined)
  }, [productQuantities, allAvailableProducts])

  // Quantity handlers
  const handleUpdateQuantity = (productId: string, delta: number) => {
    setProductQuantities((prev) => {
      const current = prev[productId] || 0
      const updated = current + delta
      const copy = { ...prev }
      if (updated <= 0) {
        delete copy[productId]
      } else {
        copy[productId] = Math.min(10, updated)
      }
      return copy
    })
  }

  const handleRemoveProduct = (productId: string) => {
    setProductQuantities((prev) => {
      const copy = { ...prev }
      delete copy[productId]
      return copy
    })
  }

  const handleAddProduct = (productId: string) => {
    setProductQuantities((prev) => ({
      ...prev,
      [productId]: (prev[productId] || 0) + 1,
    }))
    setShowAddDrawer(false)
  }

  // Strict Indian mobile phone validation (10 digits starting with 6, 7, 8, or 9)
  const isPhoneValid = useMemo(() => {
    return /^[6-9]\d{9}$/.test(phone.trim())
  }, [phone])

  const hasItems = selectedKit !== null || selectedProductsList.length > 0
  const isDatesValid = rentalDays > 0

  const isFormValid =
    hasItems &&
    isDatesValid &&
    customerName.trim().length >= 2 &&
    email.trim().length > 0 &&
    isPhoneValid

  // Form submission handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isFormValid || isSubmitting) return

    setIsSubmitting(true)
    setSubmitError(null)

    try {
      const payload: EnquirySubmissionPayload = {
        customerName: customerName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        message: message.trim() || undefined,
        productSelections,
        kitId: selectedKitId,
        startDate,
        endDate,
        durationDays: rentalDays,
        calculatedEstimate: quote.total,
      }

      const result = await submitRentalEnquiry(payload, idempotencyKey)
      setSubmissionResult(result)
    } catch (err: unknown) {
      console.error('Enquiry submission error:', err)
      const message = err instanceof Error ? err.message : 'Failed to submit rental enquiry. Please review your details and retry.'
      setSubmitError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleStartNewEnquiry = () => {
    setSubmissionResult(null)
    setSubmitError(null)
    setIdempotencyKey(typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `gs-${Date.now()}`)
  }

  // Confirmation view
  if (submissionResult) {
    const isHoldActive = submissionResult.status === 'Pending Review'
    const holdDateFormatted = submissionResult.holdExpiresAt
      ? new Date(submissionResult.holdExpiresAt).toLocaleString('en-IN', {
          dateStyle: 'medium',
          timeStyle: 'short',
        })
      : null

    return (
      <div className="mx-auto w-full max-w-[1780px]">
        <div className="mx-auto max-w-2xl border border-white/[0.08] bg-[#0c0d0e] p-8 sm:p-12 text-left">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-6">
            <div className="size-10 grid place-items-center rounded-full border border-white/20 bg-white/5 text-white">
              <Check className="size-5" />
            </div>
            <span className="font-mono text-xs uppercase tracking-widest text-[#717478]">
              REF #{submissionResult.referenceId}
            </span>
          </div>

          <div className="mt-8">
            <span className="border border-white/20 bg-white/5 px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.2em] text-white/80">
              {submissionResult.isSimulated ? 'SIMULATED DEMO ENQUIRY' : `STATUS: ${submissionResult.status.toUpperCase()}`}
            </span>
            <h1 className="font-heading mt-4 text-3xl font-medium tracking-tight text-white sm:text-4xl">
              Rental Enquiry Received.
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-[#8c9094]">
              Thank you, <strong className="text-white">{customerName}</strong>. Our equipment team will review your requested shoot timeline ({startDate} → {endDate}) and confirm equipment reservation availability shortly.
            </p>

            {/* Confirmation email notification message */}
            <div className="mt-4 pt-3 border-t border-white/10 text-xs leading-relaxed">
              {submissionResult.confirmationEmailSent ? (
                <p className="text-[#a1a5a9]">
                  Your confirmation email has been sent to <span className="text-white font-medium">{email}</span>. Please check your inbox and spam folder for your GearShare rental enquiry confirmation.
                </p>
              ) : (
                <p className="text-amber-300/90">
                  Your rental enquiry was received successfully, but we couldn&apos;t send the confirmation email. Please save your enquiry reference.
                </p>
              )}
            </div>

            {holdDateFormatted && isHoldActive && (
              <p className="mt-3 inline-flex items-center gap-2 border border-emerald-500/20 bg-emerald-950/20 px-3 py-1.5 text-xs text-emerald-300">
                <Clock className="size-3.5" />
                <span>24-Hour Inventory Hold Active until: <strong>{holdDateFormatted}</strong></span>
              </p>
            )}
          </div>

          <div className="mt-8 divide-y divide-white/[0.06] border-y border-white/[0.08] py-4 text-xs">
            <div className="flex justify-between py-2 text-[#8c9094]">
              <span>Customer</span>
              <span className="text-white font-medium">{customerName} ({email})</span>
            </div>
            <div className="flex justify-between py-2 text-[#8c9094]">
              <span>Phone</span>
              <span className="text-white font-medium">+91 {phone}</span>
            </div>
            <div className="flex justify-between py-2 text-[#8c9094]">
              <span>Rental Duration</span>
              <span className="text-white font-mono">{rentalDays} days</span>
            </div>
            <div className="flex justify-between py-2 text-[#8c9094]">
              <span>Estimated Quote</span>
              <span className="font-heading text-lg font-medium text-white">{quote.formattedTotal}</span>
            </div>
          </div>

          <div className="mt-6 text-[11px] leading-relaxed text-[#717478]">
            {submissionResult.message}
          </div>

          <div className="mt-10 flex flex-wrap gap-4">
            <Link
              href={backHref}
              className="inline-flex items-center gap-2 bg-white px-6 py-3.5 text-xs font-semibold uppercase tracking-[0.16em] text-black transition hover:bg-neutral-200"
            >
              <ArrowLeft className="size-3.5" /> Back to browsing
            </Link>
            <button
              type="button"
              onClick={handleStartNewEnquiry}
              className="border border-white/20 px-6 py-3.5 text-xs font-semibold uppercase tracking-[0.16em] text-white transition hover:border-white/50"
            >
              Configure Another Enquiry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto w-full max-w-[1780px]">
      {/* Page Header */}
      <div className="border-b border-white/[0.08] pb-10 sm:pb-14">
        <Link
          href={backHref}
          className="group inline-flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#8c9094] transition hover:text-white"
        >
          <ArrowLeft className="size-3.5 transition-transform group-hover:-translate-x-1" />
          <span>Back to browsing</span>
        </Link>

        <div className="mt-8 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <SectionLabel>09 / RENTAL ENQUIRY</SectionLabel>
            <h1 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
              Let&apos;s get your next
              <br />
              <span className="text-[#787c80]">project moving.</span>
            </h1>
          </div>
          <p className="max-w-[340px] text-sm leading-6 text-[#8c9094]">
            Configure your rental, share your details, and our team will help you with the next steps.
          </p>
        </div>
      </div>

      {/* Mobile Collapsible Sticky Summary Header */}
      <div className="mt-6 border border-white/[0.08] bg-[#0c0d0e] p-4 lg:hidden">
        <button
          type="button"
          onClick={() => setMobileSummaryOpen(!mobileSummaryOpen)}
          className="flex w-full items-center justify-between text-xs"
        >
          <div className="flex items-center gap-2">
            <span className="font-semibold uppercase tracking-wider text-white">Estimated Quote:</span>
            <span className="font-mono font-medium text-white">{quote.formattedTotal}</span>
            <span className="text-[#717478]">({rentalDays}d)</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] uppercase tracking-wider text-[#8c9094]">
            <span>{mobileSummaryOpen ? 'Hide Summary' : 'View Breakdown'}</span>
            <ChevronDown className={`size-3.5 transition-transform ${mobileSummaryOpen ? 'rotate-180' : ''}`} />
          </div>
        </button>

        {mobileSummaryOpen && (
          <div className="mt-4 border-t border-white/[0.06] pt-4 text-xs space-y-2">
            {quote.lines.map((l) => (
              <div key={l.id} className="flex justify-between text-[#8c9094]">
                <span>{l.quantity}× {l.name}</span>
                <span className="font-mono text-white">{formatINR(l.subtotal)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2-Column Responsive Layout */}
      <div className="mt-10 grid gap-12 lg:grid-cols-[1.18fr_0.82fr] xl:grid-cols-[1.24fr_0.76fr] xl:gap-16">
        {/* Left Column: Configuration & Customer Form */}
        <div className="space-y-12">
          {/* Section A: Selected Creator Kit (if active) */}
          {selectedKit && (
            <div className="border border-white/[0.08] bg-[#0c0d0e] p-6 sm:p-7">
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                  Curated Creator Kit Bundle
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedKitId(null)}
                  className="inline-flex items-center gap-1.5 text-xs text-[#8c9094] transition hover:text-white"
                >
                  <Trash2 className="size-3" /> Remove Kit
                </button>
              </div>

              <div className="mt-5 flex flex-col gap-5 sm:flex-row">
                <div className="relative aspect-video w-full sm:w-44 shrink-0 overflow-hidden border border-white/[0.08] bg-[#060708]">
                  <img
                    src={selectedKit.image}
                    alt={selectedKit.title}
                    className="size-full object-cover grayscale contrast-110"
                  />
                  <span className="absolute left-2.5 top-2.5 border border-white/20 bg-black/60 px-2 py-0.5 text-[8px] font-semibold uppercase tracking-wider text-white backdrop-blur-md">
                    {selectedKit.tag}
                  </span>
                </div>

                <div className="flex-1">
                  <h3 className="font-heading text-xl font-medium text-white">{selectedKit.title}</h3>
                  <p className="mt-1 text-xs text-[#8c9094]">{selectedKit.description}</p>
                  <p className="mt-3 font-mono text-sm font-medium text-white">
                    {formatINR(selectedKit.price)} <span className="text-xs text-[#717478]">/ day</span>
                  </p>
                </div>
              </div>

              {/* Kit items breakdown */}
              <div className="mt-6 border-t border-white/[0.06] pt-4">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#717478]">
                  Included In This Kit:
                </span>
                <ul className="mt-2.5 grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs text-[#c2c5c8]">
                  {selectedKit.includedItems.map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2">
                      <span className="size-1 rounded-full bg-white/40" />
                      <span className="text-[#8c9094]">{item.role}:</span>
                      <span className="text-white font-medium truncate">{item.name}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Section B: Selected Individual Equipment */}
          <div className="border border-white/[0.08] bg-[#0c0d0e] p-6 sm:p-7">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                Configured Equipment Items ({selectedProductsList.length})
              </span>
              <button
                type="button"
                onClick={() => setShowAddDrawer(!showAddDrawer)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-white hover:text-neutral-300"
              >
                <Plus className="size-3.5" /> {showAddDrawer ? 'Close Selector' : 'Add More Equipment'}
              </button>
            </div>

            {/* Quick Add Equipment Drawer */}
            {showAddDrawer && (
              <div className="mt-5 border border-white/[0.08] bg-[#141518] p-4">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#787c80]">
                  Select an item to add to your rental configuration:
                </span>
                <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-2 max-h-60 overflow-y-auto pr-1">
                  {allAvailableProducts.map((prod) => (
                    <button
                      key={prod.id}
                      type="button"
                      onClick={() => handleAddProduct(prod.id)}
                      className="flex items-center justify-between border border-white/10 bg-[#0c0d0e] p-2.5 text-left transition hover:border-white/40 hover:bg-[#1a1c20]"
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <img src={prod.image} alt={prod.name} className="size-8 object-cover grayscale shrink-0" />
                        <div className="truncate">
                          <p className="text-xs font-medium text-white truncate">{prod.name}</p>
                          <p className="text-[10px] text-[#717478]">{prod.category} · {formatINR(prod.price)}/d</p>
                        </div>
                      </div>
                      <Plus className="size-3.5 text-white/70 shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Selected Products List */}
            {selectedProductsList.length === 0 && !selectedKit ? (
              <div className="mt-8 py-10 text-center">
                <p className="text-sm text-[#8c9094]">
                  No equipment has been selected yet.
                </p>
                <div className="mt-4 flex justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => setShowAddDrawer(true)}
                    className="inline-flex items-center gap-2 bg-white/10 px-4 py-2 text-xs font-medium uppercase tracking-wider text-white hover:bg-white/20"
                  >
                    <Plus className="size-3" /> Add Equipment
                  </button>
                  <Link
                    href="/#gear"
                    className="inline-flex items-center gap-2 border border-white/20 px-4 py-2 text-xs font-medium uppercase tracking-wider text-white hover:border-white"
                  >
                    Explore Catalog
                  </Link>
                </div>
              </div>
            ) : (
              <div className="mt-5 divide-y divide-white/[0.06]">
                {selectedProductsList.map(({ product, quantity }) => {
                  const isCoveredByKit = kitBundledProductIds.has(product.id)
                  return (
                    <div
                      key={product.id}
                      className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="flex items-center gap-4">
                        <div className="relative aspect-square size-16 shrink-0 overflow-hidden border border-white/[0.08] bg-[#050607]">
                          <img
                            src={product.image}
                            alt={product.name}
                            className="size-full object-cover grayscale contrast-110"
                          />
                        </div>
                        <div>
                          <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-[#787c80]">
                            {product.brand} · {product.category}
                          </span>
                          <h4 className="font-heading text-sm font-medium text-white">{product.name}</h4>
                          <p className="text-xs font-mono text-[#8c9094]">
                            {formatINR(product.price)} <span className="text-[10px] text-[#717478]">/ day</span>
                          </p>
                          {isCoveredByKit && (
                            <span className="text-[9px] text-amber-300/80">
                              (Included in active kit bundle)
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Quantity & Remove */}
                      <div className="flex items-center justify-between sm:justify-end gap-5">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleUpdateQuantity(product.id, -1)}
                            className="grid size-7 place-items-center border border-white/20 text-xs text-white transition hover:border-white"
                          >
                            −
                          </button>
                          <span className="w-6 text-center text-xs font-mono text-white">{quantity}</span>
                          <button
                            type="button"
                            onClick={() => handleUpdateQuantity(product.id, 1)}
                            className="grid size-7 place-items-center border border-white/20 text-xs text-white transition hover:border-white"
                          >
                            +
                          </button>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveProduct(product.id)}
                          className="text-[#717478] transition hover:text-white"
                          title="Remove item"
                        >
                          <Trash2 className="size-4" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Section C: Rental Dates */}
          <div className="border border-white/[0.08] bg-[#0c0d0e] p-6 sm:p-7">
            <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center border-b border-white/[0.08] pb-4">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                Rental Dates & Schedule
              </span>
              {rentalDays > 0 ? (
                <span className="font-mono text-xs text-emerald-400">
                  {rentalDays} {rentalDays === 1 ? 'day rental' : 'days rental'} (inclusive)
                </span>
              ) : (
                <span className="text-xs font-mono text-amber-400">
                  Invalid date selection
                </span>
              )}
            </div>

            <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div>
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8c9094]">
                  Start Date
                </label>
                <input
                  type="date"
                  min={minDate}
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="mt-2 w-full border border-white/15 bg-[#141518] px-4 py-3 text-sm text-white outline-none transition focus:border-white focus:bg-[#1a1c20]"
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8c9094]">
                  End Date
                </label>
                <input
                  type="date"
                  min={startDate || minDate}
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="mt-2 w-full border border-white/15 bg-[#141518] px-4 py-3 text-sm text-white outline-none transition focus:border-white focus:bg-[#1a1c20]"
                />
              </div>
            </div>
          </div>

          {/* Section D: Customer Details Form */}
          <div className="border border-white/[0.08] bg-[#0c0d0e] p-6 sm:p-7">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
              Your Production Details
            </span>

            <form onSubmit={handleSubmit} className="mt-6 space-y-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8c9094]">
                    Full Name <span className="text-white/40">*</span>
                  </label>
                  <input
                    required
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="Alex Morgan"
                    className="mt-2.5 w-full border-b border-white/20 bg-transparent py-2.5 text-sm text-white outline-none transition focus:border-white"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8c9094]">
                    Email Address <span className="text-white/40">*</span>
                  </label>
                  <input
                    required
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="alex@production.com"
                    className="mt-2.5 w-full border-b border-white/20 bg-transparent py-2.5 text-sm text-white outline-none transition focus:border-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8c9094]">
                  Indian Mobile Number <span className="text-white/40">* (10 digits)</span>
                </label>
                <div className="relative mt-2.5 flex items-center border-b border-white/20 transition focus-within:border-white">
                  <span className="text-sm font-mono text-[#8c9094] pr-2 select-none">+91</span>
                  <input
                    required
                    type="tel"
                    inputMode="numeric"
                    maxLength={10}
                    value={phone}
                    onChange={(e) => {
                      const cleaned = e.target.value.replace(/\D/g, '').slice(0, 10)
                      setPhone(cleaned)
                    }}
                    placeholder="9876543210"
                    className="w-full bg-transparent py-2.5 text-sm font-mono text-white outline-none"
                  />
                </div>
                {phone.length > 0 && !isPhoneValid && (
                  <p className="mt-1.5 text-[11px] text-amber-400">
                    Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.
                  </p>
                )}
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8c9094]">
                  Additional Message / Project Scope (Optional)
                </label>
                <textarea
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Tell us about your shoot location, specialized mount needs, or scheduling details..."
                  className="mt-2.5 w-full resize-none border-b border-white/20 bg-transparent py-2.5 text-sm text-white outline-none transition focus:border-white"
                />
              </div>

              {availabilityWarning && (
                <div className="flex items-start gap-3 border border-amber-500/30 bg-amber-950/20 p-4 text-xs text-amber-200">
                  <AlertCircle className="size-4 shrink-0 text-amber-400 mt-0.5" />
                  <span>{availabilityWarning}</span>
                </div>
              )}

              {submitError && (
                <div className="flex items-start gap-3 border border-red-500/30 bg-red-950/20 p-4 text-xs text-red-200">
                  <AlertCircle className="size-4 shrink-0 text-red-400 mt-0.5" />
                  <div>
                    <strong className="block font-medium">Submission Conflict or Error</strong>
                    <span>{submitError}</span>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={!isFormValid || isSubmitting}
                className={`group mt-4 flex w-full items-center justify-center gap-3 py-4 text-xs font-semibold uppercase tracking-[0.18em] transition-all duration-300 ${
                  isFormValid && !isSubmitting
                    ? 'bg-white text-black hover:bg-neutral-200 shadow-lg shadow-white/10 cursor-pointer'
                    : 'bg-white/10 text-white/30 cursor-not-allowed'
                }`}
              >
                <span>{isSubmitting ? 'Processing Enquiry...' : 'Submit Rental Enquiry'}</span>
                <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" />
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Sticky Summary & Breakdown */}
        <div>
          <div className="sticky top-28 border border-white/[0.08] bg-[#0c0d0e] p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                Rental Summary
              </span>
              <span className="border border-white/15 px-2 py-0.5 font-mono text-[9px] uppercase tracking-wider text-white/70">
                PROVISIONAL
              </span>
            </div>

            {/* Schedule timeline */}
            <div className="mt-5 space-y-2 text-xs">
              <div className="flex justify-between text-[#8c9094]">
                <span>Timeline</span>
                <span className="text-white font-mono">
                  {startDate} → {endDate}
                </span>
              </div>
              <div className="flex justify-between text-[#8c9094]">
                <span>Duration</span>
                <span className="text-white font-mono">
                  {rentalDays > 0 ? `${rentalDays} days` : 'Invalid dates'}
                </span>
              </div>
            </div>

            {/* Line items list */}
            <div className="mt-6 border-t border-white/[0.08] pt-6">
              <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#787c80]">
                Configured Equipment ({quote.lines.length})
              </span>

              {quote.lines.length === 0 ? (
                <p className="mt-3 text-xs text-[#717478] italic">
                  No equipment currently configured.
                </p>
              ) : (
                <div className="mt-3 divide-y divide-white/[0.06] max-h-72 overflow-y-auto pr-1">
                  {quote.lines.map((line) => (
                    <div key={line.id} className="py-2.5 text-xs">
                      <div className="flex justify-between font-medium text-white">
                        <span className="truncate pr-2">
                          {line.quantity}× {line.name}
                        </span>
                        <span className="font-mono shrink-0">{formatINR(line.subtotal)}</span>
                      </div>
                      <div className="mt-0.5 flex justify-between text-[10px] text-[#717478]">
                        <span>
                          {formatINR(line.dailyRate)}/day × {line.durationDays}d
                        </span>
                        {line.type === 'kit' && <span className="uppercase text-white/50">Bundle Rate</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Calculations breakdown */}
            <div className="mt-6 space-y-2.5 border-t border-white/[0.08] pt-6 text-xs text-[#8c9094]">
              <div className="flex justify-between">
                <span>Equipment Subtotal</span>
                <span className="font-mono text-white">{formatINR(quote.subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span>Applicable Discounts</span>
                <span className="font-mono text-[#717478]">None (Net Rate)</span>
              </div>
              <div className="flex justify-between border-t border-white/10 pt-4 text-base font-medium text-white">
                <span>Estimated Total</span>
                <span className="font-heading text-2xl tracking-tight text-white font-medium">
                  {quote.formattedTotal}
                </span>
              </div>
            </div>

            {/* Verification note */}
            <p className="mt-5 text-[10px] leading-relaxed text-[#717478]">
              Final availability and pricing will be confirmed by our team after reviewing your enquiry.
            </p>

            {/* Trust Badges */}
            <div className="mt-6 space-y-2 border-t border-white/[0.08] pt-5 text-[10px] uppercase tracking-[0.16em] text-[#717478]">
              <p className="flex items-center gap-2">
                <Check className="size-3 text-white" /> Clean sensor & optics inspected prior to handoff
              </p>
              <p className="flex items-center gap-2">
                <Check className="size-3 text-white" /> Complete battery, cable & case accessories included
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function RentalEnquiryPage() {
  return (
    <main className="min-h-screen bg-[#050607] px-6 pb-16 pt-28 text-[#f4f4f2] sm:px-10 md:px-10 md:pb-24 md:pt-36 lg:px-14 xl:px-16">
      <SiteNav />
      <Suspense
        fallback={
          <div className="py-24 text-center font-mono text-xs uppercase tracking-widest text-[#717478]">
            Loading rental configuration...
          </div>
        }
      >
        <RentalEnquiryContent />
      </Suspense>
    </main>
  )
}
