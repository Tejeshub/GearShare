'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { useGLTF, Float, OrbitControls } from '@react-three/drei'
import { motion, AnimatePresence } from 'framer-motion'
import { Suspense, useEffect, useMemo, useRef, useState, Component, type ReactNode } from 'react'
import * as THREE from 'three'
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  ShieldCheck,
  X,
  Sparkles,
  Layers,
  Clock
} from 'lucide-react'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { SmoothScrollProvider } from '@/components/SmoothScrollProvider'
import { CinematicHero } from '@/components/CinematicHero'
import { SiteNav } from '@/components/SiteNav'
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
  categoriesService,
  equipmentService,
  kitsService,
  rentalsService,
  availabilityService,
  contactService,
  type CategoryResponse,
  type EquipmentResponse,
  type CreatorKitResponse,
  type CombinedAvailabilityCheckResponse,
} from '@/lib/api'


// Preload the real 3D models
if (typeof window !== 'undefined') {
  useGLTF.preload('/camera_lens.glb')
}


const images = {
  hero: 'https://images.unsplash.com/photo-1606986628253-6bcf6d5f1c2d?auto=format&fit=crop&w=1400&q=85',
  camera: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=85',
  lens: 'https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=900&q=85',
  lighting: 'https://images.unsplash.com/photo-1554048612-b6a482bc67e5?auto=format&fit=crop&w=900&q=85',
  rig: 'https://images.unsplash.com/photo-1589872307372-9c7c7c5f3c4a?auto=format&fit=crop&w=900&q=85',
  studio: 'https://images.unsplash.com/photo-1607462109225-6b64ae2dd3cb?auto=format&fit=crop&w=1400&q=85',
}

const gear = [
  { name: 'Sony FX30', brand: 'Sony', category: 'Cameras', price: 48, spec: 'Cinema Super 35 · 4K 120p', image: images.camera },
  { name: 'A7 IV', brand: 'Sony', category: 'Cameras', price: 42, spec: '33MP Full-frame · Hybrid', image: images.hero },
  { name: '24–70mm GM II', brand: 'Sony', category: 'Lenses', price: 28, spec: 'f/2.8 · G Master Zoom', image: images.lens },
  { name: 'Suction Car Mount Pro', brand: 'Tilta', category: 'Car Mount', price: 35, spec: 'Hydraulic Damping · 4.5kg Payload', image: '/images/categories/car-mount.webp' },

  { name: 'Vintage Embroidered Strap', brand: 'Artisan', category: 'Camera Strap', price: 12, spec: 'Jacquard Weave · Quick Release', image: '/images/categories/camera-strap.webp' },
  { name: 'Carbon Travel Tripod', brand: 'Ulanzi', category: 'Tripod', price: 18, spec: 'Carbon Fibre · Teleprompter Rig', image: '/images/categories/tripod.webp' },
  { name: 'DJI RS3 Pro Gimbal', brand: 'DJI', category: 'Gimbal', price: 32, spec: '3-Axis Motorized · Vertical Shooting', image: '/images/categories/gimbal.webp' },
]

const categoryData = [
  {
    name: 'Cameras',
    desc: 'Bodies built for decisive moments.',
    image: '/images/categories/cameras.webp',
    position: 'object-center',
    span: 'md:col-span-2 md:row-span-2',
  },
  {
    name: 'Lenses',
    desc: 'Glass that changes perspective.',
    image: '/images/categories/lenses.webp',
    position: 'object-center',
    span: 'md:col-span-1 md:row-span-1',
  },
  {
    name: 'Car Mount',
    desc: 'High-speed dynamic vehicle rigs.',
    image: '/images/categories/car-mount.webp',
    position: 'object-center',
    span: 'md:col-span-1 md:row-span-1',
  },
  {
    name: 'Camera Strap',
    desc: 'Ergonomic woven and leather straps.',
    image: '/images/categories/camera-strap.webp',
    position: 'object-center',
    span: 'md:col-span-1 md:row-span-1',
  },
  {
    name: 'Tripod',
    desc: 'Rock-solid support for every frame.',
    image: '/images/categories/tripod.webp',
    position: 'object-center',
    span: 'md:col-span-1 md:row-span-1',
  },
  {
    name: 'Gimbal',
    desc: 'Precision 3-axis motorized motion.',
    image: '/images/categories/gimbal.webp',
    position: 'object-center',
    span: 'md:col-span-2 md:row-span-1',
  },
]




const kits = [
  { title: 'Insta360 Luna Ultra Creator Bundle', tag: 'ULTRA 360 / IMMERSIVE', text: 'Handheld dual-lens 8K capture, touchscreen monitoring, and wireless audio.', price: 3899, image: '/images/kits/insta360-luna-ultra.webp', items: 'Insta360 Dual-Lens · Touch Display · Wireless Mic · Batteries' },
  { title: 'Content Creator Kit', tag: 'STREAMING / WORKSPACE', text: 'The complete studio streaming & video production workspace setup.', price: 4999, image: '/images/kits/content-creator-kit.webp', items: 'Sony FX30 · Ring Light Stand · Shotgun Mic · GorillaPod' },
  { title: 'Canon Content Creator Kit', tag: 'CREATOR / HYBRID', text: 'All-in-one vlogging and content kit with wireless grip and directional audio.', price: 4299, image: '/images/kits/canon-content-creator.webp', items: 'Canon EOS Body · RF-S 18–45mm · Wireless Tripod Grip · Mic' },
]




// Initial full-screen loading experience
function Preloader({ isLoaded, onAnimationComplete }: { isLoaded: boolean; onAnimationComplete: () => void }) {
  const [progress, setProgress] = useState(15)

  useEffect(() => {
    if (isLoaded) {
      setProgress(100)
    } else {
      // Natural initial progression while asset loads
      const timer = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(timer)
            return 90
          }
          return prev + Math.floor(Math.random() * 12 + 6)
        })
      }, 120)
      return () => clearInterval(timer)
    }
  }, [isLoaded])

  return (
    <AnimatePresence onExitComplete={onAnimationComplete}>
      {!isLoaded && (
        <motion.div
          key="preloader"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.85, ease: [0.16, 1, 0.3, 1] } }}
          className="fixed inset-0 z-[100] flex flex-col items-center justify-between bg-[#040506] px-8 py-12 text-[#f4f4f2]"
        >
          {/* Top metadata */}
          <div className="flex w-full max-w-[1360px] items-center justify-between text-[10px] uppercase tracking-[0.22em] text-[#6b6e72]">
            <span className="flex items-center gap-2">
              <span className="inline-block size-1.5 rounded-full bg-white/70 animate-pulse" />
              GearShare Archive
            </span>
            <span>Studio Calibration</span>
          </div>

          {/* Center Brand and Lens Aperture Animation */}
          <div className="flex flex-col items-center">
            {/* Elegant lens aperture ring */}
            <div className="relative mb-8 grid size-20 place-items-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 14, repeat: Infinity, ease: 'linear' }}
                className="absolute inset-0 rounded-full border border-dashed border-white/20"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                className="absolute inset-2 rounded-full border border-white/30"
                style={{ borderTopColor: 'transparent', borderLeftColor: 'transparent' }}
              />
              <div className="relative grid size-10 place-items-center rounded-full border border-white/40 bg-white/[0.03] backdrop-blur-sm">
                <span className="text-[11px] font-semibold tracking-wider text-white">G</span>
              </div>
            </div>

            {/* Wordmark */}
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="font-heading text-2xl font-medium tracking-[0.28em] text-[#f4f4f2] sm:text-3xl"
            >
              GEARSHARE
            </motion.h1>
            <p className="mt-2 text-[11px] uppercase tracking-[0.24em] text-[#73767a]">
              Cinematic Equipment Rentals
            </p>

            {/* Progress Bar & percentage */}
            <div className="mt-8 flex w-48 flex-col items-center gap-2 sm:w-64">
              <div className="h-[2px] w-full overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className="h-full bg-white"
                  initial={{ width: '0%' }}
                  animate={{ width: `${progress}%` }}
                  transition={{ ease: 'easeOut', duration: 0.3 }}
                />
              </div>
              <div className="flex w-full justify-between text-[9px] uppercase tracking-[0.18em] text-[#787c80]">
                <span>Preparing 3D Stage</span>
                <span>{progress}%</span>
              </div>
            </div>
          </div>

          {/* Bottom subtle note */}
          <div className="text-[10px] uppercase tracking-[0.2em] text-[#55585b]">
            Precision Glass · Cinema Bodies · Production Ready
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-5 text-[10px] uppercase tracking-[0.26em] text-[#82868a]">
      {children}
    </p>
  )
}



function Categories({ onCategory }: { onCategory: (c: string) => void }) {
  const [hoveredCategory, setHoveredCategory] = useState<string | null>(null)
  const [categories, setCategories] = useState<CategoryResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true
    categoriesService
      .getCategories()
      .then((data) => {
        if (active) {
          // Use backend category visibility metadata to determine which appear in showcase
          const visible = data.filter((c) => c.isVisibleInCategorySection)
          setCategories(visible)
          setIsLoading(false)
        }
      })
      .catch((err) => {
        console.error('Failed to load categories:', err)
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  // Static visual mapping for the 6 editorial card layouts
  const cardLayoutMeta: Record<string, { image: string; desc: string; position: string; span: string }> = {
    Cameras: {
      image: '/images/categories/cameras.webp',
      desc: 'Bodies built for decisive moments.',
      position: 'object-center',
      span: 'md:col-span-2 md:row-span-2',
    },
    Lenses: {
      image: '/images/categories/lenses.webp',
      desc: 'Glass that changes perspective.',
      position: 'object-center',
      span: 'md:col-span-1 md:row-span-1',
    },
    'Car Mount': {
      image: '/images/categories/car-mount.webp',
      desc: 'High-speed dynamic vehicle rigs.',
      position: 'object-center',
      span: 'md:col-span-1 md:row-span-1',
    },
    'Camera Strap': {
      image: '/images/categories/camera-strap.webp',
      desc: 'Ergonomic woven and leather straps.',
      position: 'object-center',
      span: 'md:col-span-1 md:row-span-1',
    },
    Tripod: {
      image: '/images/categories/tripod.webp',
      desc: 'Rock-solid support for every frame.',
      position: 'object-center',
      span: 'md:col-span-1 md:row-span-1',
    },
    Gimbal: {
      image: '/images/categories/gimbal.webp',
      desc: 'Precision 3-axis motorized motion.',
      position: 'object-center',
      span: 'md:col-span-2 md:row-span-1',
    },
  }

  // Display cards: Use live backend categories if loaded, otherwise fallback to categoryData
  const displayCards = useMemo(() => {
    if (categories.length > 0) {
      return categories.map((cat, idx) => {
        const meta = cardLayoutMeta[cat.name] || {
          image: categoryData[idx % categoryData.length]?.image || '/placeholder.webp',
          desc: cat.description || categoryData[idx % categoryData.length]?.desc || '',
          position: 'object-center',
          span: categoryData[idx % categoryData.length]?.span || 'md:col-span-1 md:row-span-1',
        }
        return {
          name: cat.name,
          slug: cat.slug,
          desc: meta.desc,
          image: meta.image,
          position: meta.position,
          span: meta.span,
          count: cat.productCount,
        }
      })
    }
    return categoryData.map((cat) => ({
      ...cat,
      slug: cat.name.toLowerCase().replace(/\s+/g, '-'),
      count: finalizedProducts.filter((p) => p.category === cat.name).length,
    }))
  }, [categories])

  return (
    <section id="categories" className="bg-[#0b0c0d] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16">
      <div className="mx-auto w-full max-w-[1780px]">
        {/* Section Header */}
        <div className="flex flex-col justify-between gap-7 md:flex-row md:items-end">
          <div>
            <SectionLabel>01 / Explore by discipline</SectionLabel>
            <h2 className="font-heading max-w-[620px] text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
              Start with the
              <br />
              <span className="text-[#787c80]">way you create.</span>
            </h2>
          </div>
          <p className="max-w-[340px] text-sm leading-6 text-[#8c9094]">
            A considered collection of tools for stills, motion, light, and sound. Precision equipment, kept shoot-ready.
          </p>
        </div>

        {/* Editorial Asymmetric Grid */}
        <div
          className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4 md:gap-5"
          onMouseLeave={() => setHoveredCategory(null)}
        >
          {displayCards.map((cat, i) => {
            const count = cat.count
            const countLabel = `${count} ${count === 1 ? 'item' : 'items'}`
            const isHovered = hoveredCategory === cat.name
            const isAnyHovered = hoveredCategory !== null

            return (
              <button
                key={cat.name}
                onClick={() => onCategory(cat.name)}
                onMouseEnter={() => setHoveredCategory(cat.name)}
                onFocus={() => setHoveredCategory(cat.name)}
                onBlur={() => setHoveredCategory(null)}
                className={`group relative min-h-[260px] overflow-hidden text-left border border-white/[0.07] bg-[#111214] transition-all duration-500 ease-out sm:min-h-[280px] ${
                  cat.span
                } ${i === 0 ? 'md:min-h-[580px]' : 'md:min-h-[280px]'} ${
                  isAnyHovered && !isHovered ? 'opacity-40 grayscale' : 'opacity-100'
                } hover:border-white/30 hover:shadow-2xl hover:shadow-black/60`}
              >
                {/* Background image with fallback */}
                <img
                  src={cat.image}
                  alt={cat.name}
                  loading="lazy"
                  onError={(e) => {
                    const target = e.currentTarget
                    target.onerror = null
                    target.src = '/placeholder.webp'
                  }}
                  className={`absolute inset-0 size-full object-cover ${cat.position} grayscale contrast-110 transition-transform duration-700 ease-out group-hover:scale-105 group-hover:grayscale-0`}
                />

                {/* Refined gradient overlay for text legibility */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#050607]/95 via-[#050607]/40 to-transparent transition-opacity duration-500 group-hover:from-[#050607]/90" />

                {/* Subtle top indicator */}
                <div className="absolute inset-x-0 top-0 flex items-center justify-between p-5 md:p-6">
                  <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/50 transition-colors duration-300 group-hover:text-white/80">
                    0{i + 1}
                  </span>
                  <div className="grid size-8 place-items-center rounded-full border border-white/10 bg-black/40 text-white/60 opacity-0 backdrop-blur-sm transition-all duration-300 group-hover:opacity-100 group-hover:text-white">
                    <ArrowUpRight className="size-3.5" />
                  </div>
                </div>

                {/* Content Box */}
                <div className="absolute inset-x-0 bottom-0 p-5 sm:p-6 md:p-7">
                  <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-white/60">
                    {countLabel}
                  </p>
                  <h3 className="mt-2 text-2xl font-medium tracking-[-0.03em] text-[#f4f4f2] sm:text-3xl">
                    {cat.name}
                  </h3>
                  <p className="mt-1.5 max-w-[280px] text-xs font-normal leading-relaxed text-white/70 opacity-90 transition-opacity duration-300 group-hover:opacity-100">
                    {cat.desc}
                  </p>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function Gear({ selected, setSelected }: { selected: string; setSelected: (v: string) => void }) {
  const [equipmentList, setEquipmentList] = useState<EquipmentResponse[]>([])
  const [active, setActive] = useState<Product | EquipmentResponse | null>(null)
  const [modalQty, setModalQty] = useState(1)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let activeEffect = true
    equipmentService
      .getEquipment({ featured: true, limit: 50 })
      .then((res) => {
        if (activeEffect) {
          setEquipmentList(res.items)
          setIsLoading(false)
        }
      })
      .catch((err) => {
        console.error('Failed to load featured equipment:', err)
        if (activeEffect) setIsLoading(false)
      })
    return () => {
      activeEffect = false
    }
  }, [])

  // Use live equipment if loaded, otherwise fallback to finalizedProducts
  const allProducts: Array<Product | EquipmentResponse> = equipmentList.length > 0 ? equipmentList : finalizedProducts

  const filtered = selected === 'All' ? allProducts : allProducts.filter((p) => p.category === selected)

  // Dynamically derive category filters from available items + defaults
  const filters = useMemo(() => {
    const defaultFilters = ['All', 'Cameras', 'Lenses', 'Car Mount', 'Camera Strap', 'Tripod', 'Gimbal']
    const catSet = new Set<string>()
    allProducts.forEach((p) => catSet.add(p.category))
    defaultFilters.forEach((f) => catSet.add(f))
    return Array.from(catSet)
  }, [allProducts])

  const openModal = (product: Product | EquipmentResponse) => {
    setActive(product)
    setModalQty(1)
  }

  return (
    <section id="gear" className="bg-[#050607] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16">
      <div className="mx-auto w-full max-w-[1780px]">
        {/* Section Header */}
        <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
          <div>
            <SectionLabel>02 / Featured equipment</SectionLabel>
            <h2 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
              The right tool
              <br />
              <span className="text-[#787c80]">changes everything.</span>
            </h2>
          </div>
          <p className="max-w-[340px] text-sm leading-6 text-[#8c9094]">
            Calibrated cinema cameras, G Master optics, and pro studio lighting. Kept in pristine condition, priced transparently.
          </p>
        </div>

        {/* Category Filter Tabs */}
        <div className="mt-12 flex flex-wrap gap-2 border-y border-white/10 py-4">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setSelected(f)}
              className={`px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] transition-all duration-300 ${
                selected === f
                  ? 'bg-white text-black shadow-lg shadow-white/10'
                  : 'text-[#8c9094] hover:bg-white/[0.04] hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* 4-Column Product Catalog Grid */}
        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 lg:gap-6">
          {filtered.map((item) => (
            <article
              key={item.id}
              onClick={() => openModal(item)}
              className="group relative flex flex-col justify-between border border-white/[0.08] bg-[#0c0d0e] p-4 transition-all duration-500 hover:border-white/30 hover:bg-[#111214] hover:shadow-2xl hover:shadow-black/70 cursor-pointer"
            >
              {/* Product Photograph Container */}
              <div className="relative aspect-[4/3] w-full overflow-hidden bg-[#060708]">
                <img
                  src={item.image}
                  alt={item.name}
                  loading="lazy"
                  className="size-full object-cover object-center grayscale contrast-110 transition-transform duration-700 ease-out group-hover:scale-105 group-hover:grayscale-0"
                />
                {/* Availability Badge */}
                <div className="absolute left-3 top-3 flex items-center gap-1.5 border border-white/20 bg-black/60 px-2.5 py-1 text-[9px] font-medium uppercase tracking-[0.14em] text-white/90 backdrop-blur-md">
                  <span className="size-1.5 rounded-full bg-emerald-400" />
                  {item.availability}
                </div>

                {/* Quick Details Hover Icon */}
                <div className="absolute bottom-3 right-3 grid size-9 translate-y-2 place-items-center bg-white text-black opacity-0 shadow-lg transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100">
                  <ArrowUpRight className="size-4" />
                </div>
              </div>

              {/* Card Meta & Details */}
              <div className="mt-4 flex flex-1 flex-col justify-between pt-1">
                <div>
                  <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-[0.18em] text-[#787c80]">
                    <span>{item.brand}</span>
                    <span>{item.category}</span>
                  </div>
                  <h3 className="mt-1.5 font-heading text-lg font-medium tracking-tight text-[#f4f4f2] group-hover:text-white">
                    {item.name}
                  </h3>
                  <p className="mt-1 text-xs text-[#8c9094] line-clamp-1">{item.spec}</p>
                </div>

                {/* Pricing & CTA */}
                <div className="mt-5 flex items-center justify-between border-t border-white/[0.08] pt-3.5">
                  <div>
                    <span className="text-[10px] uppercase tracking-[0.14em] text-[#63676b]">Daily Rate</span>
                    <p className="font-heading text-base font-semibold text-[#f4f4f2]">
                      ₹{item.price.toLocaleString('en-IN')}{' '}
                      <span className="text-[11px] font-normal text-[#787c80]">/ day</span>
                    </p>
                  </div>

                  <span className="border border-white/20 px-3 py-1.5 text-[10px] font-medium uppercase tracking-[0.14em] text-white/80 transition-colors group-hover:border-white group-hover:bg-white group-hover:text-black">
                    View Details
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>

        {/* Empty State for categories without matching products */}
        {filtered.length === 0 && (
          <div className="my-16 border border-white/10 bg-[#0c0d0e] p-12 text-center">
            <p className="text-xs uppercase tracking-[0.2em] text-[#717478]">Inventory Notice</p>
            <h3 className="mt-2 font-heading text-xl font-medium text-white">
              No equipment currently listed under {selected}
            </h3>
            <p className="mx-auto mt-2 max-w-md text-sm text-[#8c9094]">
              We are actively refreshing our specialized catalog. Contact our team to enquire about custom requests.
            </p>
            <button
              onClick={() => setSelected('All')}
              className="mt-6 border border-white/30 px-5 py-2.5 text-xs uppercase tracking-[0.16em] text-white transition hover:bg-white hover:text-black"
            >
              View All Equipment
            </button>
          </div>
        )}
      </div>

      {/* Product Detail Modal */}
      {active && (
        <div
          className="fixed inset-0 z-[80] grid place-items-center bg-black/85 p-4 backdrop-blur-md sm:p-6"
          onClick={() => setActive(null)}
        >
          <div
            className="relative max-h-[90vh] w-full max-w-3xl overflow-y-auto border border-white/15 bg-[#101113] p-6 sm:p-8"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={() => setActive(null)}
              aria-label="Close product modal"
              className="absolute right-5 top-5 grid size-9 place-items-center border border-white/15 text-white/70 transition hover:border-white hover:text-white"
            >
              <X className="size-4" />
            </button>

            <div className="grid gap-8 md:grid-cols-2">
              {/* Left Column: High-Res Image */}
              <div className="relative aspect-square w-full overflow-hidden border border-white/10 bg-[#060708]">
                <img
                  src={active.image}
                  alt={active.name}
                  className="size-full object-cover grayscale contrast-110"
                />
                <div className="absolute left-3 top-3 flex items-center gap-1.5 border border-white/20 bg-black/60 px-2.5 py-1 text-[9px] uppercase tracking-[0.14em] text-white/90 backdrop-blur-md">
                  <span className="size-1.5 rounded-full bg-emerald-400" />
                  {active.availability}
                </div>
              </div>

              {/* Right Column: Detailed Specifications & Action */}
              <div className="flex flex-col justify-between">
                <div>
                  <SectionLabel>
                    {active.category} / {active.brand}
                  </SectionLabel>
                  <h3 className="font-heading text-3xl font-medium tracking-tight text-white">{active.name}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#9a9ea2]">{active.description}</p>

                  {/* Bulleted Specifications */}
                  <div className="mt-5 border-t border-white/10 pt-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#787c80]">
                      Key Specifications
                    </p>
                    <ul className="mt-2.5 space-y-1.5 text-xs text-[#c5c8cb]">
                      {active.specs.map((s, idx) => (
                        <li key={idx} className="flex items-center gap-2">
                          <Check className="size-3 text-white/60" />
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Pricing Display */}
                  <div className="mt-6 border-t border-white/10 pt-4">
                    <p className="text-[10px] uppercase tracking-[0.16em] text-[#717478]">Daily Rental Price</p>
                    <p className="font-heading mt-1 text-2xl font-semibold text-white">
                      ₹{active.price.toLocaleString('en-IN')}{' '}
                      <span className="text-sm font-normal text-[#787c80]">/ day</span>
                    </p>
                  </div>

                  {/* Quantity Selector */}
                  <div className="mt-4 flex items-center gap-4">
                    <span className="text-xs uppercase tracking-[0.14em] text-[#8c9094]">Quantity:</span>
                    <div className="flex items-center border border-white/20">
                      <button
                        type="button"
                        onClick={() => setModalQty(Math.max(1, modalQty - 1))}
                        className="grid size-8 place-items-center text-white transition hover:bg-white/10"
                      >
                        −
                      </button>
                      <span className="w-8 text-center text-xs font-semibold text-white">{modalQty}</span>
                      <button
                        type="button"
                        onClick={() => setModalQty(modalQty + 1)}
                        className="grid size-8 place-items-center text-white transition hover:bg-white/10"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>

                {/* Primary Action Button navigating to /rental-enquiry */}
                <Link
                  href={`/rental-enquiry?product=${encodeURIComponent(active.id)}&qty=${modalQty}&origin=gear`}
                  className="mt-8 flex w-full items-center justify-center gap-2 bg-white py-3.5 text-center text-xs font-semibold uppercase tracking-[0.16em] text-black transition-all duration-300 hover:bg-neutral-200"
                >
                  <span>Rent This Gear</span>
                  <ArrowRight className="size-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

function Kits() {
  const [kitsList, setKitsList] = useState<CreatorKitResponse[]>([])
  const [active, setActive] = useState<CreatorKit | CreatorKitResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let activeEffect = true
    kitsService
      .getKits()
      .then((data) => {
        if (activeEffect) {
          setKitsList(data)
          setIsLoading(false)
        }
      })
      .catch((err) => {
        console.error('Failed to load creator kits:', err)
        if (activeEffect) setIsLoading(false)
      })
    return () => {
      activeEffect = false
    }
  }, [])

  const displayKits: Array<CreatorKit | CreatorKitResponse> = kitsList.length > 0 ? kitsList : creatorKits

  return (
    <section id="kits" className="border-t border-white/[0.08] bg-[#0c0d0e] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16">
      <div className="mx-auto w-full max-w-[1780px]">
        {/* Section Header */}
        <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <SectionLabel>03 / Creator kits</SectionLabel>
            <h2 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
              Built for the way
              <br />
              <span className="text-[#787c80]">you create.</span>
            </h2>
          </div>
          <p className="max-w-[340px] text-sm leading-6 text-[#8c9094]">
            Skip the guesswork. Our considered bundles bring the right combination of camera, glass, lighting, and support together for the work ahead.
          </p>
        </div>

        {/* Asymmetric 3-Card Grid */}
        <div className="mt-14 grid gap-5 sm:gap-6 md:grid-cols-2 lg:grid-cols-[1.12fr_0.88fr]">
          {displayKits.map((kit, i) => (
            <button
              key={kit.id}
              onClick={() => setActive(kit)}
              className={`group relative overflow-hidden text-left border border-white/[0.08] bg-[#111214] transition-all duration-500 hover:border-white/30 hover:shadow-2xl hover:shadow-black/70 ${
                i === 0
                  ? 'min-h-[460px] sm:min-h-[520px] md:col-span-2 lg:col-span-1 lg:row-span-2 lg:min-h-[640px]'
                  : 'min-h-[300px] sm:min-h-[320px] md:col-span-1 lg:min-h-[306px]'
              }`}
            >
              {/* Kit Photograph with subtle dark treatment */}
              <img
                src={kit.image}
                alt={kit.title}
                loading="lazy"
                className="absolute inset-0 size-full object-cover object-center grayscale contrast-110 transition-transform duration-700 ease-out group-hover:scale-105 group-hover:grayscale-0"
              />

              {/* Multi-layer gradient overlay for pristine text contrast */}
              <div className="absolute inset-0 bg-gradient-to-t from-[#050607]/95 via-[#050607]/45 to-transparent transition-opacity duration-500 group-hover:from-[#050607]/90" />

              {/* Top Tag & Item Count Badge */}
              <div className="absolute inset-x-0 top-0 flex items-center justify-between p-6 sm:p-7">
                <span className="border border-white/20 bg-black/50 px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.18em] text-white/90 backdrop-blur-md">
                  {kit.tag}
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/60">
                  {kit.includedItems.length} ITEMS INCLUDED
                </span>
              </div>

              {/* Bottom Content */}
              <div className="absolute inset-x-0 bottom-0 p-6 sm:p-7 lg:p-8">
                <h3 className={`font-heading font-medium tracking-tight text-white transition-colors group-hover:text-white ${
                  i === 0 ? 'text-2xl sm:text-3xl lg:text-4xl' : 'text-xl sm:text-2xl'
                }`}>
                  {kit.title}
                </h3>
                <p className="mt-2 max-w-md text-xs sm:text-sm leading-relaxed text-[#c2c5c8] line-clamp-2">
                  {kit.description}
                </p>

                {/* Pricing & CTA Line */}
                <div className="mt-5 flex items-center justify-between border-t border-white/20 pt-4 text-xs">
                  <div>
                    <span className="text-[10px] uppercase tracking-[0.14em] text-[#8c9094]">Bundle Rate</span>
                    <p className="font-heading text-lg font-semibold text-white">
                      ₹{kit.price.toLocaleString('en-IN')}{' '}
                      <span className="text-xs font-normal text-[#8c9094]">/ day</span>
                    </p>
                  </div>

                  <span className="inline-flex items-center gap-1.5 border border-white/20 px-3.5 py-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-white transition-all duration-300 group-hover:border-white group-hover:bg-white group-hover:text-black">
                    <span>Explore Kit</span>
                    <ArrowUpRight className="size-3.5" />
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Kit Detail Modal */}
      {active && (
        <div
          className="fixed inset-0 z-[80] grid place-items-center bg-black/85 p-4 backdrop-blur-md sm:p-6"
          onClick={() => setActive(null)}
        >
          <div
            className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto border border-white/15 bg-[#101113] p-6 sm:p-8"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={() => setActive(null)}
              aria-label="Close kit modal"
              className="absolute right-5 top-5 grid size-9 place-items-center border border-white/15 text-white/70 transition hover:border-white hover:text-white"
            >
              <X className="size-4" />
            </button>

            {/* Header Image */}
            <div className="relative aspect-[16/9] w-full overflow-hidden border border-white/10 bg-[#060708]">
              <img
                src={active.image}
                alt={active.title}
                className="size-full object-cover grayscale contrast-110"
              />
              <div className="absolute left-3 top-3 border border-white/20 bg-black/60 px-2.5 py-1 text-[9px] uppercase tracking-[0.16em] text-white/90 backdrop-blur-md">
                {active.tag}
              </div>
            </div>

            {/* Content Meta */}
            <div className="mt-6">
              <SectionLabel>Curated Creator Bundle</SectionLabel>
              <h3 className="font-heading text-3xl font-medium tracking-tight text-white">{active.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#9a9ea2]">{active.description}</p>

              {/* Intended Use Banner */}
              <div className="mt-4 border-l-2 border-white/30 bg-white/[0.03] p-3 text-xs text-[#d2d4d6]">
                <span className="font-semibold text-white">Intended Use: </span>
                {active.intendedUse}
              </div>

              {/* Complete Equipment Inclusions */}
              <div className="mt-6 border-t border-white/10 pt-4">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#787c80]">
                    Complete Equipment Included ({active.includedItems.length} items)
                  </p>
                  <span className="text-[10px] uppercase tracking-[0.14em] text-white/60">Ready to Shoot</span>
                </div>

                <div className="mt-3 divide-y divide-white/10 border border-white/10 bg-[#0c0d0e]">
                  {active.includedItems.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3.5 text-xs">
                      <span className="font-medium text-[#8c9094]">{item.role}</span>
                      <span className="font-medium text-white">{item.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pricing & Booking Action */}
              <div className="mt-7 flex flex-col gap-4 border-t border-white/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <span className="text-[10px] uppercase tracking-[0.14em] text-[#717478]">Combined Bundle Price</span>
                  <p className="font-heading text-2xl font-semibold text-white">
                    ₹{active.price.toLocaleString('en-IN')}{' '}
                    <span className="text-sm font-normal text-[#787c80]">/ day</span>
                  </p>
                </div>

                <Link
                  href={`/rental-enquiry?kit=${encodeURIComponent(active.id)}&qty=1&origin=kits`}
                  className="inline-flex items-center justify-center gap-2 bg-white px-6 py-3.5 text-xs font-semibold uppercase tracking-[0.16em] text-black transition hover:bg-neutral-200"
                >
                  <span>Rent This Creator Kit</span>
                  <ArrowRight className="size-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

function Process() {
  const steps = [
    {
      step: '01',
      title: 'Discover',
      desc: 'Explore professional equipment for your next project.',
    },
    {
      step: '02',
      title: 'Choose',
      desc: 'Select an individual item or a considered Creator Kit.',
    },
    {
      step: '03',
      title: 'Enquire',
      desc: 'Share your dates and requirements with our team.',
    },
    {
      step: '04',
      title: 'Shoot',
      desc: 'Receive your equipment and make something memorable.',
    },
  ]

  return (
    <section id="process" className="border-t border-white/[0.08] bg-[#050607] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16">
      <div className="mx-auto w-full max-w-[1780px]">
        {/* Section Header */}
        <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <SectionLabel>05 / HOW IT WORKS</SectionLabel>
            <h2 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
              From idea to image, simply.
            </h2>
          </div>
          <p className="max-w-[340px] text-sm leading-6 text-[#8c9094]">
            No friction between the idea and the making of it.
          </p>
        </div>

        {/* Timeline Container */}
        <div className="mt-16 sm:mt-20 md:mt-24">
          {/* Desktop Timeline (Horizontal) */}
          <div className="hidden md:block">
            {/* Connecting Track & Markers Bar */}
            <div className="relative flex items-center justify-between">
              {/* Thin connecting background track */}
              <div className="absolute left-[24px] right-[24px] top-1/2 h-[1px] -translate-y-1/2 bg-white/[0.12]" />

              {/* Animated reveal line */}
              <motion.div
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }}
                style={{ originX: 0 }}
                className="absolute left-[24px] right-[24px] top-1/2 h-[1px] -translate-y-1/2 bg-gradient-to-r from-white/40 via-white/70 to-white/30"
              />

              {/* Step Markers */}
              {steps.map((item, idx) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, scale: 0.7 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.5, delay: idx * 0.18, ease: 'easeOut' }}
                  className="group relative z-10 flex size-12 items-center justify-center rounded-full border border-white/20 bg-[#0c0d0e] transition-all duration-300 hover:border-white/60 hover:bg-[#16171a]"
                >
                  <span className="font-mono text-xs font-semibold tracking-wider text-white/90 transition-colors group-hover:text-white">
                    {item.step}
                  </span>
                  <div className="absolute -inset-1 rounded-full border border-white/0 transition-all duration-300 group-hover:border-white/10" />
                </motion.div>
              ))}
            </div>

            {/* Step Content 4-Column Grid */}
            <div className="mt-10 grid grid-cols-4 gap-8 xl:gap-12">
              {steps.map((item, idx) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.6, delay: 0.2 + idx * 0.16, ease: [0.16, 1, 0.3, 1] }}
                  className="pr-4"
                >
                  <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                    Phase {item.step}
                  </div>
                  <h3 className="mt-2 text-xl font-medium tracking-tight text-white xl:text-2xl">
                    {item.title}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#8c9094]">
                    {item.desc}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Mobile Timeline (Vertical Sequence) */}
          <div className="relative md:hidden">
            {/* Vertical connecting line */}
            <div className="absolute bottom-6 left-5 top-5 w-[1px] bg-white/[0.12]" />
            <motion.div
              initial={{ scaleY: 0 }}
              whileInView={{ scaleY: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
              style={{ originY: 0 }}
              className="absolute bottom-6 left-5 top-5 w-[1px] bg-gradient-to-b from-white/40 via-white/70 to-white/20"
            />

            <div className="flex flex-col space-y-10">
              {steps.map((item, idx) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: '-30px' }}
                  transition={{ duration: 0.5, delay: idx * 0.15, ease: 'easeOut' }}
                  className="relative flex items-start gap-5 pl-2"
                >
                  {/* Number marker */}
                  <div className="relative z-10 flex size-9 shrink-0 items-center justify-center rounded-full border border-white/20 bg-[#0c0d0e]">
                    <span className="font-mono text-[11px] font-semibold text-white/90">
                      {item.step}
                    </span>
                  </div>

                  {/* Text details */}
                  <div className="pt-0.5">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                      Step {item.step}
                    </div>
                    <h3 className="mt-1 text-lg font-medium tracking-tight text-white">
                      {item.title}
                    </h3>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#8c9094]">
                      {item.desc}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Why() {
  const benefits = [
    {
      title: 'Quality Checked, Every Time',
      desc: 'Equipment condition and details are presented clearly.',
    },
    {
      title: 'Transparent Pricing',
      desc: 'Understand your estimated costs before you enquire.',
    },
    {
      title: 'Flexible Rental Periods',
      desc: 'Choose a duration suited to your project.',
    },
    {
      title: 'Curated Creator Kits',
      desc: 'Ready-made combinations for specific creative needs.',
    },
  ]

  return (
    <section id="why" className="border-t border-white/[0.08] bg-[#0b0c0d] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16">
      <div className="mx-auto w-full max-w-[1780px]">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16 xl:gap-24">
          {/* Left Column: Heading & Benefits List */}
          <div>
            <SectionLabel>06 / ABOUT GEARSHARE</SectionLabel>
            <h2 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
              About
              <br />
              <span className="text-[#787c80]">GearShare.</span>
            </h2>
            <p className="mt-6 max-w-xl text-sm leading-6 text-[#8c9094] sm:text-base">
              GearShare is built for creators, photographers, and filmmakers who believe great stories deserve great equipment.
            </p>
            <p className="mt-4 max-w-xl text-sm leading-6 text-[#8c9094] sm:text-base">
              We make professional photography and filmmaking gear accessible through flexible rental options, carefully curated equipment, and creator-focused kits.
            </p>
            <p className="mt-4 max-w-xl text-sm leading-6 text-[#8c9094] sm:text-base">
              Whether you're working on a personal project, a commercial shoot, or your next big creative idea, GearShare helps you get the right gear without the commitment of ownership.
            </p>

            <div className="mt-10 divide-y divide-white/[0.08] border-y border-white/[0.08]">
              {benefits.map((item, idx) => (
                <div
                  key={item.title}
                  className="group flex items-start gap-6 py-5 transition-colors duration-300 hover:bg-white/[0.02]"
                >
                  <span className="font-mono text-xs font-semibold tracking-wider text-[#717478] transition-colors group-hover:text-white">
                    0{idx + 1}
                  </span>
                  <div>
                    <h3 className="text-base font-medium text-[#f4f4f2] transition-colors group-hover:text-white sm:text-lg">
                      {item.title}
                    </h3>
                    <p className="mt-1.5 text-xs sm:text-sm leading-relaxed text-[#8c9094]">
                      {item.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Premium Equipment Photograph */}
          <div className="relative aspect-[4/5] sm:aspect-[1/1] lg:aspect-[4/5] xl:aspect-[1/1] w-full overflow-hidden border border-white/[0.08] bg-[#050607]">
            <img
              src="/images/why-gearshare/studio-rig.webp"
              alt="Professional cinema camera rig with anamorphic lens and studio monitoring setup"
              loading="lazy"
              className="size-full object-cover object-center grayscale contrast-115 transition-transform duration-700 ease-out hover:scale-105"
            />
            {/* Subtle monochrome vignette and depth gradients */}
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#050607]/90 via-black/25 to-transparent" />
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-tr from-black/40 via-transparent to-black/30" />

            {/* Editorial Caption */}
            <div className="absolute inset-x-0 bottom-0 flex items-center justify-between p-6 sm:p-7 backdrop-blur-[2px]">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/80">
                Studio & Cinema Production Rigs
              </span>
              <span className="font-mono text-[9px] uppercase tracking-widest text-white/50">
                CALIBRATED · SHOOT-READY
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Calculator() {
  const router = useRouter()

  // Default dates: tomorrow until 3 days later
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() + 4)
    return d.toISOString().split('T')[0]
  })

  // Selected Creator Kit (optional)
  const [selectedKitId, setSelectedKitId] = useState<string | null>(null)

  // Selected product quantities: map of productId -> quantity
  const [productQuantities, setProductQuantities] = useState<Record<string, number>>({
    'sony-fx30': 1,
  })

  // State: dynamic rentable equipment and kits loaded from backend
  const [rentableList, setRentableList] = useState<EquipmentResponse[]>([])
  const [kitsList, setKitsList] = useState<CreatorKitResponse[]>([])
  const [availabilityReport, setAvailabilityReport] = useState<CombinedAvailabilityCheckResponse | null>(null)
  const [isQuoteLoading, setIsQuoteLoading] = useState(false)
  const [serverQuote, setServerQuote] = useState<RentalQuoteResponse | null>(null)

  useEffect(() => {
    let active = true
    equipmentService
      .getEquipment({ rentable: true, limit: 50 })
      .then((res) => {
        if (active && res.items.length > 0) setRentableList(res.items)
      })
      .catch((err) => console.error('Failed to load rentable equipment:', err))

    kitsService
      .getKits()
      .then((data) => {
        if (active && data.length > 0) setKitsList(data)
      })
      .catch((err) => console.error('Failed to load kits in calculator:', err))

    return () => {
      active = false
    }
  }, [])

  // Available equipment & kits with fallback to static constants
  const availableEquipment: Array<Product | EquipmentResponse> = rentableList.length > 0 ? rentableList : calculatorProducts
  const availableKits: Array<CreatorKit | CreatorKitResponse> = kitsList.length > 0 ? kitsList : creatorKits

  // Currently selected kit object
  const activeKit = useMemo(() => {
    if (!selectedKitId) return null
    return availableKits.find((k) => k.id === selectedKitId) || null
  }, [selectedKitId, availableKits])

  // Set of product IDs bundled in the active kit
  const kitBundledProductIds = useMemo(() => {
    if (!activeKit) return new Set<string>()
    return new Set(activeKit.productIds || [])
  }, [activeKit])

  // Toggle or change kit selection
  const handleSelectKit = (kitId: string) => {
    if (selectedKitId === kitId) {
      setSelectedKitId(null)
    } else {
      setSelectedKitId(kitId)
    }
  }

  // Toggle individual product selection
  const handleToggleProduct = (productId: string) => {
    setProductQuantities((prev) => {
      const copy = { ...prev }
      if (copy[productId]) {
        delete copy[productId]
      } else {
        copy[productId] = 1
      }
      return copy
    })
  }

  // Update product quantity
  const handleSetQuantity = (productId: string, qty: number) => {
    if (qty <= 0) {
      setProductQuantities((prev) => {
        const copy = { ...prev }
        delete copy[productId]
        return copy
      })
    } else {
      setProductQuantities((prev) => ({
        ...prev,
        [productId]: Math.min(10, qty),
      }))
    }
  }

  // Compute rental duration
  const rentalDays = useMemo(() => calculateRentalDays(startDate, endDate), [startDate, endDate])

  const productSelections = useMemo(() => {
    return Object.entries(productQuantities).map(([productId, quantity]) => ({
      productId,
      quantity,
    }))
  }, [productQuantities])

  // Local provisional calculation for immediate responsive preview
  const localQuote: RentalQuoteResponse = useMemo(() => {
    return calculateRentalQuote({
      productSelections,
      kitId: selectedKitId,
      startDate,
      endDate,
    })
  }, [productSelections, selectedKitId, startDate, endDate])

  // Backend Authoritative Quote & Availability Check (Debounced)
  useEffect(() => {
    if (rentalDays <= 0 || (productSelections.length === 0 && !selectedKitId)) {
      setServerQuote(null)
      setAvailabilityReport(null)
      return
    }

    const abortController = new AbortController()
    setIsQuoteLoading(true)

    const timer = setTimeout(() => {
      // 1. Fetch server quote
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
          console.error('Server quote calculation failed, using local preview:', err)
          setIsQuoteLoading(false)
        })

      // 2. Fetch date-wise availability check
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
          setAvailabilityReport(res)
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

  // Authoritative quote: use serverQuote when available, local preview otherwise
  const quote = serverQuote || localQuote

  // Validation
  const hasItems = quote.lines.length > 0
  const isDateValid = rentalDays > 0
  const canContinue = hasItems && isDateValid

  // Navigate to /rental-enquiry with complete prepopulation parameters
  const handleContinue = () => {
    if (!canContinue) return

    const params = new URLSearchParams()
    if (selectedKitId) {
      params.set('kit', selectedKitId)
    }
    // Pass selected products and quantities
    const selectedEntries = Object.entries(productQuantities).filter(([, q]) => q > 0)
    if (selectedEntries.length > 0) {
      // Primary product for single-item view
      params.set('product', selectedEntries[0][0])
      params.set('qty', selectedEntries[0][1].toString())
      // All selected items encoded
      const itemsPayload = selectedEntries.map(([id, q]) => `${id}:${q}`).join(',')
      params.set('items', itemsPayload)
    }
    params.set('startDate', startDate)
    params.set('endDate', endDate)
    params.set('days', rentalDays.toString())
    params.set('origin', 'calculator')

    router.push(`/rental-enquiry?${params.toString()}`)
  }

  // Today string for minimum date selection
  const minDate = useMemo(() => new Date().toISOString().split('T')[0], [])

  // Map of unavailable product IDs from availability report
  const unavailableProductIds = useMemo(() => {
    const set = new Set<string>()
    if (availabilityReport?.products) {
      availabilityReport.products.forEach((p) => {
        if (!p.isAvailable) set.add(p.productId)
      })
    }
    return set
  }, [availabilityReport])

  return (
    <section id="calculator" className="border-t border-white/[0.08] bg-[#050607] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16">
      <div className="mx-auto w-full max-w-[1780px]">
        {/* Section Header */}
        <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <SectionLabel>07 / RENTAL ESTIMATE</SectionLabel>
            <h2 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
              Plan your rental.
              <br />
              <span className="text-[#787c80]">Know your estimate.</span>
            </h2>
          </div>
          <p className="max-w-[340px] text-sm leading-6 text-[#8c9094]">
            Choose your equipment and duration. This estimate is a guide; final availability and pricing are confirmed after enquiry.
          </p>
        </div>

        {/* 2-Column Responsive Layout */}
        <div className="mt-14 grid gap-10 lg:grid-cols-[1.15fr_0.85fr] xl:grid-cols-[1.25fr_0.75fr] xl:gap-14">
          {/* Left Column: Dates, Kits, & Equipment Catalog */}
          <div className="space-y-12">
            {/* 1. Date Selection Bar */}
            <div className="border border-white/[0.08] bg-[#0b0c0e] p-6 sm:p-7">
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                  Step 01 / Rental Schedule
                </span>
                {rentalDays > 0 ? (
                  <span className="inline-flex items-center gap-1.5 text-xs font-mono text-emerald-400">
                    <span className="size-1.5 rounded-full bg-emerald-400" />
                    {rentalDays} {rentalDays === 1 ? 'day rental' : 'days rental'} (inclusive)
                  </span>
                ) : (
                  <span className="text-xs font-mono text-amber-400">
                    End date must be on or after start date
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

            {/* 2. Creator Kit Quick-Select Bundles */}
            <div>
              <div className="mb-4 flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                  Step 02 / Curated Creator Kits (Optional)
                </span>
                {selectedKitId && (
                  <button
                    onClick={() => setSelectedKitId(null)}
                    className="text-[11px] uppercase tracking-wider text-[#8c9094] underline hover:text-white"
                  >
                    Clear Kit Selection
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {availableKits.map((kit) => {
                  const isSelected = selectedKitId === kit.id
                  return (
                    <button
                      key={kit.id}
                      type="button"
                      onClick={() => handleSelectKit(kit.id)}
                      className={`group relative flex flex-col justify-between border p-5 text-left transition-all duration-300 ${
                        isSelected
                          ? 'border-white bg-[#16171a] shadow-lg shadow-white/5'
                          : 'border-white/[0.08] bg-[#0c0d0e] hover:border-white/25 hover:bg-[#111214]'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-white/60">
                            {kit.tag}
                          </span>
                          <span
                            className={`grid size-4 place-items-center rounded-sm border ${
                              isSelected ? 'border-white bg-white text-black' : 'border-white/20'
                            }`}
                          >
                            {isSelected && <Check className="size-3" />}
                          </span>
                        </div>
                        <h4 className="mt-2.5 font-heading text-base font-medium text-white">
                          {kit.title}
                        </h4>
                        <p className="mt-1 text-xs text-[#8c9094] line-clamp-2">
                          {kit.description}
                        </p>
                      </div>

                      <div className="mt-4 border-t border-white/[0.08] pt-3 text-xs">
                        <span className="font-mono text-white">{formatINR(kit.price)}</span>
                        <span className="text-[10px] text-[#717478]"> / day</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* 3. Finalized 8 Products Grid */}
            <div>
              <div className="mb-4 flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                  Step 03 / Select Individual Equipment
                </span>
                <span className="text-[11px] uppercase tracking-wider text-[#717478]">
                  8 Shoot-Ready Items
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-2 xl:grid-cols-2">
                {availableEquipment.map((product) => {
                  const isSelected = !!productQuantities[product.id]
                  const quantity = productQuantities[product.id] || 0
                  const isCoveredByKit = kitBundledProductIds.has(product.id)
                  const isDateUnavailable = unavailableProductIds.has(product.id)

                  return (
                    <div
                      key={product.id}
                      className={`group relative flex flex-col justify-between border p-4 transition-all duration-300 ${
                        isSelected
                          ? 'border-white/80 bg-[#141518]'
                          : 'border-white/[0.08] bg-[#0c0d0e] hover:border-white/25'
                      }`}
                    >
                      <div className="flex gap-4">
                        {/* Thumbnail */}
                        <div className="relative aspect-square w-20 shrink-0 overflow-hidden border border-white/[0.08] bg-[#050607]">
                          <img
                            src={product.image}
                            alt={product.name}
                            loading="lazy"
                            className="size-full object-cover grayscale contrast-110 transition-transform duration-500 group-hover:scale-105"
                          />
                        </div>

                        {/* Details */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-[#787c80]">
                                {product.brand} · {product.category}
                              </span>
                              <h4 className="mt-0.5 font-heading text-sm font-medium text-white truncate">
                                {product.name}
                              </h4>
                            </div>
                            {/* Checkbox */}
                            <button
                              type="button"
                              onClick={() => handleToggleProduct(product.id)}
                              className={`grid size-5 shrink-0 place-items-center rounded-sm border transition ${
                                isSelected
                                  ? 'border-white bg-white text-black'
                                  : 'border-white/25 hover:border-white'
                              }`}
                              title={isSelected ? 'Deselect item' : 'Select item'}
                            >
                              {isSelected && <Check className="size-3.5" />}
                            </button>
                          </div>

                          <div className="mt-2 flex items-center justify-between">
                            <span className="text-xs font-mono font-medium text-white">
                              {formatINR(product.price)}
                              <span className="text-[10px] text-[#717478]"> / day</span>
                            </span>
                            {isDateUnavailable ? (
                              <span className="inline-flex items-center gap-1 text-[9px] uppercase tracking-wider text-rose-400">
                                <span className="size-1 rounded-full bg-rose-400" />
                                Unavailable
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[9px] uppercase tracking-wider text-emerald-400">
                                <span className="size-1 rounded-full bg-emerald-400" />
                                {product.availability}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* If included in selected kit */}
                      {isCoveredByKit && (
                        <div className="mt-3 border-t border-white/[0.06] pt-2 text-[10px] text-amber-300/80">
                          Included in selected {activeKit?.title}
                        </div>
                      )}

                      {/* Quantity Selector (when selected) */}
                      {isSelected && (
                        <div className="mt-3.5 flex items-center justify-between border-t border-white/[0.08] pt-3">
                          <span className="text-[10px] uppercase tracking-wider text-[#8c9094]">
                            Quantity
                          </span>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleSetQuantity(product.id, quantity - 1)}
                              className="grid size-6 place-items-center border border-white/20 text-xs text-white transition hover:border-white"
                            >
                              −
                            </button>
                            <span className="w-6 text-center text-xs font-mono text-white">
                              {quantity}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleSetQuantity(product.id, quantity + 1)}
                              className="grid size-6 place-items-center border border-white/20 text-xs text-white transition hover:border-white"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Sticky Summary & Breakdown */}
          <div>
            <div className="sticky top-28 border border-white/[0.08] bg-[#0c0d0e] p-6 sm:p-8">
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                  Provisional Rental Quote
                </span>
                <span className="border border-white/15 px-2 py-0.5 font-mono text-[9px] uppercase tracking-wider text-white/70">
                  {isQuoteLoading ? 'CALCULATING...' : 'ESTIMATE ONLY'}
                </span>
              </div>

              {/* Dates & Schedule */}
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

              {/* Itemized Line Items */}
              <div className="mt-6 border-t border-white/[0.08] pt-6">
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#787c80]">
                  Configured Equipment ({quote.lines.length})
                </span>

                {quote.lines.length === 0 ? (
                  <p className="mt-4 text-xs text-[#717478] italic">
                    Select a Creator Kit or choose equipment items on the left to see itemized subtotals.
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

              {/* Calculation Summary */}
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

              {/* Notice */}
              <p className="mt-4 text-[10px] leading-relaxed text-[#717478]">
                Prices are provisional and subject to scheduling confirmation, verification, and refundable deposit terms.
              </p>

              {/* Continue to Rental Enquiry Action */}
              <button
                type="button"
                onClick={handleContinue}
                disabled={!canContinue}
                className={`group mt-6 flex w-full items-center justify-center gap-2.5 py-4 text-xs font-semibold uppercase tracking-[0.18em] transition-all duration-300 ${
                  canContinue
                    ? 'bg-white text-black hover:bg-neutral-200 shadow-lg shadow-white/10 cursor-pointer'
                    : 'bg-white/10 text-white/30 cursor-not-allowed'
                }`}
              >
                <span>Continue to Rental Enquiry</span>
                <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function FAQ() {
  const [activeCategory, setActiveCategory] = useState<'General' | 'Rentals & Pricing' | 'Equipment & Care'>('General')
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const faqData: Record<
    'General' | 'Rentals & Pricing' | 'Equipment & Care',
    Array<{ q: string; a: string }>
  > = {
    General: [
      {
        q: 'What is GearShare?',
        a: 'GearShare is a curated equipment rental service dedicated to photographers, cinematographers, and creators. We provide shoot-ready professional cameras, lenses, lighting, and stabilizers with transparent daily rates and zero guesswork.',
      },
      {
        q: 'How does the rental process work?',
        a: 'Explore our catalog or Creator Kits, configure your dates and equipment in the estimate calculator, and submit a rental enquiry. Our equipment team verifies schedule availability and prepares a personalized quote for your shoot.',
      },
      {
        q: 'What equipment can I rent?',
        a: 'We offer an editorial selection of cinema bodies, full-frame hybrid mirrorless cameras, prime and zoom optics, motorized gimbals, car mounts, studio LED fixtures, and production accessories.',
      },
      {
        q: 'Can I rent individual items or complete Creator Kits?',
        a: 'Both. You can rent a single specific lens or camera body, build a bespoke custom package, or select one of our considered Creator Kits assembled specifically for portraiture, streaming, or film production.',
      },
    ],
    'Rentals & Pricing': [
      {
        q: 'How far in advance should I enquire?',
        a: 'We recommend submitting your enquiry as soon as your shooting schedule is confirmed. This gives our team the best opportunity to reserve and calibrate your preferred kit.',
      },
      {
        q: 'Are the displayed prices final?',
        a: 'The figures in the calculator are indicative estimate rates in INR. Final pricing and availability are verified and confirmed after our team reviews your dates and shoot requirements.',
      },
      {
        q: 'How is the rental estimate calculated?',
        a: 'Item subtotals are calculated as Daily Rental Rate × Quantity × Inclusive Rental Days. The total estimate reflects the sum of selected equipment lines without hidden surcharges.',
      },
      {
        q: 'Can I change my rental dates?',
        a: 'Yes. If your shooting schedule shifts, let our team know as early as possible so we can adjust your reservation based on equipment availability.',
      },
      {
        q: 'What happens after I submit an enquiry?',
        a: 'Our equipment team reviews your requested dates and gear list, verifies inventory status, and responds with a confirmed schedule, equipment breakdown, and finalized rental quote.',
      },
    ],
    'Equipment & Care': [
      {
        q: 'Is the equipment checked before every rental?',
        a: 'Yes. Every sensor, mount, optical element, and battery undergoes rigorous functional testing and sensor cleaning before handoff to ensure shoot-ready reliability.',
      },
      {
        q: 'What condition can I expect the equipment to be in?',
        a: 'All equipment is maintained in professional, calibrated condition with clean optical surfaces, updated firmware, and all necessary cables, batteries, and protective cases.',
      },
      {
        q: 'What should I do if equipment has an issue?',
        a: 'If you encounter any unexpected technical behavior on set, contact our team immediately. We provide prompt remote troubleshooting or dispatch a replacement where feasible.',
      },
      {
        q: 'Can I request specific equipment models?',
        a: 'Yes. You can specify exact camera models, lenses, or specialized mounts directly within your rental enquiry, and our team will work to accommodate your production needs.',
      },
    ],
  }

  const currentQuestions = faqData[activeCategory]

  return (
    <section id="faq" className="border-t border-white/[0.08] bg-[#0c0d0e] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16">
      <div className="mx-auto w-full max-w-[1780px]">
        <div className="grid gap-12 lg:grid-cols-[0.82fr_1.18fr] lg:gap-16 xl:gap-24">
          {/* Left Column: Heading, Navigation Categories & Contact Card */}
          <div className="flex flex-col justify-between">
            <div>
              <SectionLabel>08 / FAQ</SectionLabel>
              <h2 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
                Good to know.
              </h2>
              <p className="mt-5 max-w-md text-sm leading-relaxed text-[#8c9094] sm:text-base">
                Everything you need to know before choosing your equipment and planning your rental.
              </p>

              {/* Three Category Selectors */}
              <div className="mt-10 flex flex-col space-y-2">
                {(['General', 'Rentals & Pricing', 'Equipment & Care'] as const).map((cat) => {
                  const isActive = activeCategory === cat
                  return (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => {
                        setActiveCategory(cat)
                        setOpenIndex(0)
                      }}
                      className={`group flex items-center justify-between border px-5 py-4 text-left transition-all duration-300 ${
                        isActive
                          ? 'border-white/80 bg-white/[0.06] text-white shadow-lg shadow-white/5'
                          : 'border-white/[0.08] bg-[#111214] text-[#8c9094] hover:border-white/25 hover:text-white'
                      }`}
                    >
                      <span className="text-xs font-semibold uppercase tracking-[0.16em]">
                        {cat}
                      </span>
                      <span
                        className={`text-xs font-mono transition-transform duration-300 ${
                          isActive ? 'text-white translate-x-1' : 'text-[#717478]'
                        }`}
                      >
                        0{faqData[cat].length}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Compact Contact Card */}
            <div className="mt-12 border border-white/[0.08] bg-[#111214] p-6 sm:p-7">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#717478]">
                Got Questions?
              </span>
              <h3 className="mt-2 font-heading text-lg font-medium text-white">
                Can&apos;t find what you&apos;re looking for?
              </h3>
              <p className="mt-1.5 text-xs leading-relaxed text-[#8c9094]">
                Get in touch with our team for custom kit requests and shoot scheduling.
              </p>
              <a
                href="#enquiry"
                className="group mt-5 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-white underline underline-offset-4 transition hover:text-neutral-300"
              >
                <span>Contact Us</span>
                <ArrowRight className="size-3 transition-transform group-hover:translate-x-1" />
              </a>
            </div>
          </div>

          {/* Right Column: Interactive Accordion */}
          <div>
            <div className="divide-y divide-white/[0.08] border-y border-white/[0.08]">
              {currentQuestions.map((item, index) => {
                const isOpen = openIndex === index
                return (
                  <div key={item.q} className="transition-colors duration-200">
                    <button
                      type="button"
                      onClick={() => setOpenIndex(isOpen ? null : index)}
                      aria-expanded={isOpen}
                      className="flex w-full items-center justify-between py-6 text-left transition-colors duration-200 hover:text-white"
                    >
                      <span className={`text-base font-medium tracking-tight sm:text-lg ${
                        isOpen ? 'text-white' : 'text-[#e5e7eb]'
                      }`}>
                        {item.q}
                      </span>
                      <span className="ml-4 grid size-8 shrink-0 place-items-center rounded-full border border-white/10 bg-white/[0.03] text-[#9ca3af] transition-colors group-hover:border-white/30">
                        <ChevronDown
                          className={`size-4 transition-transform duration-300 ${
                            isOpen ? 'rotate-180 text-white' : ''
                          }`}
                        />
                      </span>
                    </button>
                    <AnimatePresence initial={false}>
                      {isOpen && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                          className="overflow-hidden"
                        >
                          <p className="pb-6 text-sm leading-relaxed text-[#8c9094] sm:text-base sm:leading-7">
                            {item.a}
                          </p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Enquiry() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !email.trim() || !message.trim() || isSubmitting) return

    setIsSubmitting(true)
    setStatusMessage(null)

    try {
      await contactService.submitContactMessage({
        name: name.trim(),
        email: email.trim(),
        message: message.trim(),
      })
      setStatusMessage({
        type: 'success',
        text: 'Thank you — your enquiry has been received. Our team will get back to you shortly.',
      })
      setName('')
      setEmail('')
      setMessage('')
    } catch (err: unknown) {
      console.error('Failed to submit contact message:', err)
      const errorText = err instanceof Error ? err.message : 'Unable to submit enquiry. Please try again.'
      setStatusMessage({
        type: 'error',
        text: errorText,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section id="enquiry" className="border-t border-white/[0.08] bg-[#050607] px-6 py-24 sm:px-10 md:py-32 lg:px-14 xl:px-16 text-[#f4f4f2]">
      <div className="mx-auto grid w-full max-w-[1780px] gap-14 md:grid-cols-[0.9fr_1.1fr] md:gap-24">
        <div>
          <SectionLabel>09 / Start a conversation</SectionLabel>
          <h2 className="font-heading text-4xl font-medium tracking-[-0.04em] text-[#f4f4f2] sm:text-5xl md:text-6xl">
            Make the next
            <br />
            <span className="text-[#787c80]">frame count.</span>
          </h2>
          <p className="mt-6 max-w-sm text-sm leading-6 text-[#8c9094]">
            Tell us what you are making and when you need it. We will help shape the right selection.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="grid gap-5">
          <div className="grid gap-5 md:grid-cols-2">
            <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#a0a4a8]">
              Your name
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-3 w-full border-b border-white/20 bg-transparent py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-white"
                placeholder="Alex Morgan"
              />
            </label>
            <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#a0a4a8]">
              Email address
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-3 w-full border-b border-white/20 bg-transparent py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-white"
                placeholder="alex@example.com"
              />
            </label>
          </div>
          <label className="text-xs font-semibold uppercase tracking-[0.14em] text-[#a0a4a8]">
            What are you making?
            <textarea
              required
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="mt-3 min-h-28 w-full resize-none border-b border-white/20 bg-transparent py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-white"
              placeholder="A short film, editorial, campaign..."
            />
          </label>

          {statusMessage && (
            <div
              className={`p-3 text-xs leading-relaxed border ${
                statusMessage.type === 'success'
                  ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300'
                  : 'border-red-500/30 bg-red-950/20 text-red-300'
              }`}
            >
              {statusMessage.text}
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-t border-white/10 pt-6">
            <p className="text-xs text-[#717478]">Direct equipment desk enquiry.</p>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-6 py-3.5 text-xs font-semibold uppercase tracking-[0.16em] transition ${
                isSubmitting
                  ? 'bg-neutral-600 text-neutral-300 cursor-not-allowed'
                  : 'bg-white text-black hover:bg-neutral-200 cursor-pointer'
              }`}
            >
              {isSubmitting ? 'Sending...' : 'Send enquiry'} <ArrowRight className="ml-2 inline size-3" />
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}

export default function Page() {
  const [selected, setSelected] = useState('All')
  const [is3DReady, setIs3DReady] = useState(false)
  const [preloaderFinished, setPreloaderFinished] = useState(false)

  // Safety fallback in case asset fails or browser pauses rendering
  useEffect(() => {
    const safetyTimer = setTimeout(() => {
      setIs3DReady(true)
    }, 4500)
    return () => clearTimeout(safetyTimer)
  }, [])

  const onCategory = (c: string) => {
    setSelected(c)
    document.getElementById('gear')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <SmoothScrollProvider>
      <main className="bg-[#050607] text-[#f4f4f2] selection:bg-[#f4f4f2] selection:text-[#050607]">
        {/* Full screen initial loading experience */}
        {!preloaderFinished && (
          <Preloader isLoaded={is3DReady} onAnimationComplete={() => setPreloaderFinished(true)} />
        )}

        <SiteNav />
        <CinematicHero onReady={() => setIs3DReady(true)} />
        <Categories onCategory={onCategory} />
        <Gear selected={selected} setSelected={setSelected} />
        <Kits />
        <Process />
        <Why />
        <Calculator />
        <FAQ />
        <Enquiry />

        <footer className="border-t border-white/[0.08] bg-[#050607] px-6 py-12 text-[#717478] sm:px-10 lg:px-14 xl:px-16">
          <div className="mx-auto flex w-full max-w-[1780px] flex-col justify-between gap-6 text-[10px] uppercase tracking-[0.2em] md:flex-row">
            <span className="font-medium text-[#f4f4f2]">GEARSHARE / Make more.</span>
            <span>Curated Photography & Cinema Gear Rentals</span>
            <span>© GearShare · 2026</span>
          </div>
        </footer>
      </main>
    </SmoothScrollProvider>
  )
}
