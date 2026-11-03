'use client'

import { usePathname } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, Menu, X } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useLenis } from '@/components/SmoothScrollProvider'

export function SiteNav() {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()
  const lenis = useLenis()

  const sectionHref = (section: string) => pathname === '/' ? `#${section}` : `/#${section}`

  const scrollToSection = useCallback((section: string) => {
    const target = document.getElementById(section)
    if (!target) return

    if (lenis) {
      lenis.scrollTo(target)
    } else {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [lenis])

  useEffect(() => {
    if (pathname !== '/') return
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!lenis && !prefersReducedMotion) return

    const scrollToCurrentHash = () => {
      const section = window.location.hash.slice(1)
      if (section) scrollToSection(section)
    }

    const frame = window.requestAnimationFrame(scrollToCurrentHash)
    window.addEventListener('hashchange', scrollToCurrentHash)
    window.addEventListener('popstate', scrollToCurrentHash)

    return () => {
      window.cancelAnimationFrame(frame)
      window.removeEventListener('hashchange', scrollToCurrentHash)
      window.removeEventListener('popstate', scrollToCurrentHash)
    }
  }, [pathname, scrollToSection])

  const handleSectionClick = (event: React.MouseEvent<HTMLAnchorElement>, section: string) => {
    setOpen(false)
    if (pathname !== '/') return

    event.preventDefault()
    window.history.pushState(null, '', `/#${section}`)
    scrollToSection(section)
  }

  const links = [
    { section: 'gear', label: 'Explore Gear' },
    { section: 'kits', label: 'Creator Kits' },
    { section: 'process', label: 'How It Works' },
    { section: 'why', label: 'About Us' },
  ]

  return (
    <header className="fixed top-0 z-50 w-full border-b border-white/[0.07] bg-[#050607]/85 backdrop-blur-xl">
      <div className="mx-auto flex h-[76px] w-full max-w-[1780px] items-center justify-between px-6 sm:px-10 lg:px-14 xl:px-16">
        <a href="/#top" className="flex items-center gap-3.5 text-xs font-semibold tracking-[0.22em] text-[#f4f4f2]">
          <span className="grid size-7 place-items-center border border-white/40 text-[10px] font-medium tracking-tight">G</span>
          GEARSHARE
        </a>

        <nav className="hidden items-center gap-10 text-[11px] font-medium uppercase tracking-[0.18em] text-[#9a9ea2] lg:flex">
          {links.map(({ section, label }) => (
            <a key={section} href={sectionHref(section)} onClick={(event) => handleSectionClick(event, section)} className="transition-colors hover:text-white">
              {label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <a href="/#calculator" className="group hidden items-center gap-2 border border-white/20 bg-white/[0.03] px-5 py-2.5 text-[11px] font-medium uppercase tracking-[0.16em] text-[#f4f4f2] transition-all duration-300 hover:border-white hover:bg-white hover:text-black sm:flex">
            <span>Explore Equipment</span>
            <ArrowRight className="size-3.5 transition-transform duration-300 group-hover:translate-x-0.5" />
          </a>
          <button aria-label="Toggle navigation menu" aria-expanded={open} onClick={() => setOpen(!open)} className="grid size-10 place-items-center border border-white/15 text-white transition-colors hover:border-white/40 lg:hidden">
            {open ? <X className="size-4" /> : <Menu className="size-4" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.nav initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="flex flex-col gap-5 border-t border-white/10 bg-[#080909] px-6 py-8 text-xs uppercase tracking-[0.18em] lg:hidden">
            {links.map(({ section, label }) => (
              <a key={section} href={sectionHref(section)} onClick={(event) => handleSectionClick(event, section)} className="text-[#a1a1a1] hover:text-white">
                {label}
              </a>
            ))}
            <a href="/#calculator" onClick={() => setOpen(false)} className="mt-4 inline-block border border-white/30 py-3 text-center text-white">
              Explore Equipment →
            </a>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  )
}
