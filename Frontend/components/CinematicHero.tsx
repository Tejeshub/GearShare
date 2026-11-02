'use client'

import React, { useRef, useMemo, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { useGLTF } from '@react-three/drei'
import * as THREE from 'three'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  ArrowRight,
  ChevronDown,
  Sparkles,
  Layers,
  Aperture,
  Check,
  Shield,
  Focus,
  Package,
  Layers as LayersIcon,
  ShieldCheck,
  Camera,
  Maximize2
} from 'lucide-react'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

// -------------------------------------------------------------
// Scene Props
// -------------------------------------------------------------
interface SceneProps {
  progressRef: React.RefObject<number>
  mouseRef: React.MutableRefObject<{ x: number; y: number }>
  onReady?: () => void
}

// -------------------------------------------------------------
// 3D LENS SCENE COMPONENT
// Pure, focused 3D experience with the user's camera_lens.glb as centerpiece
// Optical axis is along local X: front glass at -2.45, rear mount at +2.48.
// -------------------------------------------------------------
function LensScene({ progressRef, mouseRef, onReady }: SceneProps) {
  const { scene } = useGLTF('/camera_lens.glb')

  const lensGroupRef = useRef<THREE.Group>(null)
  const lensFloatRef = useRef<THREE.Group>(null)
  const readyCalled = useRef(false)

  // Exact set of the 216 optical glass triangle indices identified by texture alpha = 0
  const GLASS_TRIANGLES = useMemo(() => new Set<number>([
    2624, 2625, 2626, 2627, 2628, 2629, 2630, 2631, 2632, 2633, 2634, 2635, 2637, 2816, 2818, 2819, 2820, 2821, 2822, 2823,
    2824, 2825, 2826, 2827, 2829, 3010, 3011, 3012, 3013, 3014, 3015, 3016, 3017, 3018, 3019, 3021, 6365, 6366, 6367, 6368,
    6369, 6370, 6371, 6372, 6373, 6374, 6375, 6376, 6377, 6378, 6379, 6380, 6381, 6382, 6383, 6384, 6385, 6386, 6387, 6388,
    6389, 6390, 6391, 6392, 6556, 6557, 6558, 6559, 6560, 6561, 6562, 6563, 6564, 6565, 6566, 6567, 6568, 6569, 6570, 6571,
    6572, 6573, 6574, 6575, 6576, 6577, 6578, 6579, 6580, 9326, 9327, 9328, 9329, 9330, 9331, 9332, 9333, 9334, 9335, 9336,
    9337, 9338, 9339, 9340, 9341, 9342, 9343, 9344, 9345, 9346, 9347, 9348, 9349, 9350, 9351, 9352, 9353, 9354, 9355, 9356,
    9357, 9358, 9359, 9360, 9361, 9362, 9363, 9364, 9365, 9366, 9367, 10936, 10938, 10939, 10940, 10941, 10942, 10943, 10944, 10945,
    10946, 10947, 10948, 10949, 10950, 10951, 10952, 10953, 10954, 10955, 10956, 10957, 10958, 10959, 10960, 10961, 10962, 10963, 10964, 10965,
    10966, 10967, 10968, 10969, 10970, 10971, 10972, 10973, 10974, 10975, 10976, 10977, 10978, 10979, 10980, 10981, 11276, 11277, 11278, 11279,
    11280, 11281, 11282, 11283, 11284, 11285, 11286, 11287, 11288, 11289, 11290, 11291, 11292, 11293, 11294, 11295, 11296, 11297, 11298, 11299,
    11470, 11472, 11473, 11474, 11475, 11476, 11477, 11478, 11479, 11480, 11481, 11482, 11483, 11484, 11485, 11486
  ]), [])

  // Center, normalize scale, and separate opaque body from optical glass
  const normalizedModel = useMemo(() => {
    const clone = scene.clone(true)
    const box = new THREE.Box3().setFromObject(clone)
    const size = new THREE.Vector3()
    box.getSize(size)
    const center = new THREE.Vector3()
    box.getCenter(center)

    // Maximum dimension is ~4.936 (from -2.454 to +2.482 along X)
    const maxDim = Math.max(size.x, size.y, size.z) || 1
    const targetSize = 2.75
    const scaleFactor = targetSize / maxDim

    // Center model precisely at origin
    clone.position.set(-center.x * scaleFactor, -center.y * scaleFactor, -center.z * scaleFactor)
    clone.scale.setScalar(scaleFactor)

    // Separate the single blended mesh into:
    // 1. Solid opaque chassis/barrel (12,372 triangles) with full depth write and no transparency
    // 2. Optical glass elements (216 triangles) with realistic transmission, clearcoat and specular reflections
    const meshesToProcess: THREE.Mesh[] = []
    clone.traverse((child) => {
      if ((child as THREE.Mesh).isMesh && child.name !== 'CameraLens_OpticalGlass') {
        meshesToProcess.push(child as THREE.Mesh)
      }
    })

    for (const mesh of meshesToProcess) {
      const geom = mesh.geometry

      if (geom && geom.index) {
        const originalIndices = geom.index.array
        const totalTris = originalIndices.length / 3

        const opaqueIdxList: number[] = []
        const glassIdxList: number[] = []

        for (let t = 0; t < totalTris; t++) {
          const i0 = originalIndices[t * 3]
          const i1 = originalIndices[t * 3 + 1]
          const i2 = originalIndices[t * 3 + 2]

          if (GLASS_TRIANGLES.has(t)) {
            glassIdxList.push(i0, i1, i2)
          } else {
            opaqueIdxList.push(i0, i1, i2)
          }
        }

        const originalMat = (Array.isArray(mesh.material) ? mesh.material[0] : mesh.material) as THREE.MeshStandardMaterial

        // 1. Truly Opaque Lens Body Material (Solves see-through barrel and backside bleed)
        const opaqueMat = originalMat.clone()
        opaqueMat.transparent = false
        opaqueMat.opacity = 1.0
        opaqueMat.depthWrite = true
        opaqueMat.depthTest = true
        opaqueMat.roughness = 0.28
        opaqueMat.metalness = 0.85
        opaqueMat.envMapIntensity = 2.2
        opaqueMat.needsUpdate = true

        // 2. Realistic Optical Glass Material (Front & Internal Optics)
        const glassMat = new THREE.MeshPhysicalMaterial({
          color: new THREE.Color('#0a1612'),
          emissive: new THREE.Color('#02140c'),
          emissiveIntensity: 0.15,
          roughness: 0.04,
          metalness: 0.05,
          transmission: 0.92,
          ior: 1.58,
          thickness: 0.8,
          specularIntensity: 2.8,
          reflectivity: 0.95,
          clearcoat: 1.0,
          clearcoatRoughness: 0.04,
          transparent: true,
          opacity: 0.88,
          depthWrite: false,
          depthTest: true,
          envMapIntensity: 3.0,
        })

        // Create separate geometry for opaque body
        const opaqueGeom = geom.clone()
        opaqueGeom.setIndex(new THREE.BufferAttribute(new Uint32Array(opaqueIdxList), 1))

        // Create separate geometry for glass
        const glassGeom = geom.clone()
        glassGeom.setIndex(new THREE.BufferAttribute(new Uint32Array(glassIdxList), 1))

        // Configure primary mesh as opaque body
        mesh.geometry = opaqueGeom
        mesh.material = opaqueMat
        mesh.castShadow = true
        mesh.receiveShadow = true
        mesh.renderOrder = 0

        // Create and append glass sub-mesh
        const glassMesh = new THREE.Mesh(glassGeom, glassMat)
        glassMesh.name = 'CameraLens_OpticalGlass'
        glassMesh.renderOrder = 1
        glassMesh.castShadow = false
        glassMesh.receiveShadow = true
        mesh.add(glassMesh)
      }
    }

    return clone
  }, [scene, GLASS_TRIANGLES])

  useEffect(() => {
    if (!readyCalled.current && onReady) {
      readyCalled.current = true
      onReady()
    }
  }, [onReady])

  // -------------------------------------------------------------
  // CONTINUOUS 5-STAGE SCROLL & MOUSE CHOREOGRAPHY
  // -------------------------------------------------------------
  useFrame((state, delta) => {
    if (!lensGroupRef.current) return

    const p = progressRef.current ?? 0
    const mouse = mouseRef.current ?? { x: 0, y: 0 }

    // Transform variables across stages
    let targetX = 0.52
    let targetY = -0.04
    let targetZ = 0.0

    // Rotations (with -Math.PI/2 offset so front glass faces +Z towards camera)
    const baseRotY = -Math.PI / 2
    let targetRotX = 0.12
    let targetRotY = baseRotY + 0.38
    let targetRotZ = 0.0

    let targetScale = 1.15
    let targetFovDist = 5.2

    if (p <= 0.20) {
      // -----------------------------------------------------------
      // INITIAL HERO (0.00 -> 0.20): Lens positioned prominently on the right
      // Large, recognizable, subtle continuous rotation & floating
      // -----------------------------------------------------------
      const t = p / 0.20
      targetX = THREE.MathUtils.lerp(0.52, 0.44, t)
      targetY = THREE.MathUtils.lerp(-0.04, -0.02, t)
      targetZ = 0.0

      targetRotX = THREE.MathUtils.lerp(0.12, 0.15, t)
      targetRotY = baseRotY + THREE.MathUtils.lerp(0.38, 0.58, t)
      targetRotZ = 0.0

      targetScale = THREE.MathUtils.lerp(1.15, 1.25, t)
      targetFovDist = 5.2
    } else if (p <= 0.40) {
      // -----------------------------------------------------------
      // STAGE 01 — EXPLORE EVERY DETAIL (0.20 -> 0.40)
      // Controlled camera push-in, moves closer, revealing barrel & surface details
      // -----------------------------------------------------------
      const t = (p - 0.20) / 0.20
      targetX = THREE.MathUtils.lerp(0.44, 0.22, t)
      targetY = THREE.MathUtils.lerp(-0.02, 0.03, t)
      targetZ = THREE.MathUtils.lerp(0.0, 1.15, t)

      targetRotX = THREE.MathUtils.lerp(0.15, 0.22, t)
      targetRotY = baseRotY + THREE.MathUtils.lerp(0.58, 1.15, t)
      targetRotZ = THREE.MathUtils.lerp(0.0, -0.04, t)

      targetScale = THREE.MathUtils.lerp(1.25, 1.35, t)
      targetFovDist = THREE.MathUtils.lerp(5.2, 4.8, t)
    } else if (p <= 0.60) {
      // -----------------------------------------------------------
      // STAGE 02 — PRECISION IN EVERY FRAME (0.40 -> 0.60)
      // Smooth 180 degrees rotation across stage revealing rear mount, rings, and construction
      // -----------------------------------------------------------
      const t = (p - 0.40) / 0.20
      targetX = THREE.MathUtils.lerp(0.22, -0.15, t)
      targetY = THREE.MathUtils.lerp(0.03, 0.0, t)
      targetZ = THREE.MathUtils.lerp(1.15, 0.75, t)

      targetRotX = THREE.MathUtils.lerp(0.22, 0.14, t)
      // 180 degrees (~Math.PI) rotation progression
      targetRotY = baseRotY + THREE.MathUtils.lerp(1.15, 1.15 + Math.PI, t)
      targetRotZ = THREE.MathUtils.lerp(-0.04, 0.02, t)

      targetScale = THREE.MathUtils.lerp(1.35, 1.28, t)
      targetFovDist = THREE.MathUtils.lerp(4.8, 5.0, t)
    } else if (p <= 0.80) {
      // -----------------------------------------------------------
      // STAGE 03 — A CLOSER PERSPECTIVE (0.60 -> 0.80)
      // Cinematic macro close-up towards front glass, beautiful optical depth, no clipping
      // -----------------------------------------------------------
      const t = (p - 0.60) / 0.20
      targetX = THREE.MathUtils.lerp(-0.15, 0.12, t)
      targetY = THREE.MathUtils.lerp(0.0, 0.05, t)
      // Controlled close distance, front glass safely framed
      targetZ = THREE.MathUtils.lerp(0.75, 1.75, t)

      targetRotX = THREE.MathUtils.lerp(0.14, 0.08, t)
      // Facing directly towards viewer
      targetRotY = baseRotY + THREE.MathUtils.lerp(1.15 + Math.PI, Math.PI * 2 + 0.15, t)
      targetRotZ = 0.0

      targetScale = THREE.MathUtils.lerp(1.28, 1.45, t)
      targetFovDist = THREE.MathUtils.lerp(5.0, 4.6, t)
    } else {
      // -----------------------------------------------------------
      // STAGE 04 & 05 — BUILD YOUR CREATOR KIT / YOUR NEXT STORY (0.80 -> 1.00)
      // Camera smooth pull-back, reposition to elegant three-quarter product showcase
      // -----------------------------------------------------------
      const t = (p - 0.80) / 0.20
      targetX = THREE.MathUtils.lerp(0.12, 0.50, t)
      targetY = THREE.MathUtils.lerp(0.05, -0.04, t)
      targetZ = THREE.MathUtils.lerp(1.75, 0.1, t)

      targetRotX = THREE.MathUtils.lerp(0.08, 0.14, t)
      targetRotY = baseRotY + THREE.MathUtils.lerp(Math.PI * 2 + 0.15, Math.PI * 2 + 0.42, t)
      targetRotZ = 0.0

      targetScale = THREE.MathUtils.lerp(1.45, 1.18, t)
      targetFovDist = THREE.MathUtils.lerp(4.6, 5.3, t)
    }

    // Subtle gentle mouse parallax (restrained and non-distracting)
    const mouseParallaxX = mouse.x * 0.08
    const mouseParallaxY = -mouse.y * 0.06
    const mouseRotParallaxY = mouse.x * 0.14
    const mouseRotParallaxX = -mouse.y * 0.10

    // Smooth damping on root lens group
    lensGroupRef.current.position.x = THREE.MathUtils.damp(
      lensGroupRef.current.position.x,
      targetX + mouseParallaxX,
      5.5,
      delta
    )
    lensGroupRef.current.position.y = THREE.MathUtils.damp(
      lensGroupRef.current.position.y,
      targetY + mouseParallaxY,
      5.5,
      delta
    )
    lensGroupRef.current.position.z = THREE.MathUtils.damp(
      lensGroupRef.current.position.z,
      targetZ,
      5.5,
      delta
    )

    lensGroupRef.current.rotation.x = THREE.MathUtils.damp(
      lensGroupRef.current.rotation.x,
      targetRotX + mouseRotParallaxX,
      5.5,
      delta
    )
    lensGroupRef.current.rotation.y = THREE.MathUtils.damp(
      lensGroupRef.current.rotation.y,
      targetRotY + mouseRotParallaxY,
      5.5,
      delta
    )
    lensGroupRef.current.rotation.z = THREE.MathUtils.damp(
      lensGroupRef.current.rotation.z,
      targetRotZ,
      5.5,
      delta
    )

    lensGroupRef.current.scale.setScalar(
      THREE.MathUtils.damp(lensGroupRef.current.scale.x, targetScale, 5.5, delta)
    )

    // Continuous subtle floating animation
    if (lensFloatRef.current) {
      lensFloatRef.current.position.y = Math.sin(state.clock.elapsedTime * 1.3) * 0.025
      lensFloatRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.6) * 0.035
    }

    // Smooth camera distance damping
    state.camera.position.z = THREE.MathUtils.damp(state.camera.position.z, targetFovDist, 5, delta)
  })

  return (
    <group ref={lensGroupRef} position={[0.52, -0.04, 0]}>
      <group ref={lensFloatRef}>
        <group rotation={[0, -Math.PI / 2, 0]}>
          <primitive object={normalizedModel} />
        </group>

        {/* Internal optical amber reflection core */}
        <pointLight
          position={[0, 0, 0.2]}
          intensity={4.5}
          color="#ff8822"
          distance={1.8}
          decay={2}
        />
      </group>
    </group>
  )
}

// -------------------------------------------------------------
// DRAMATIC STUDIO LIGHTING SETUP
// Carefully balanced rim, key, and fill lights that reveal lens rings & glass
// -------------------------------------------------------------
function StudioLighting({ progressRef }: { progressRef: React.RefObject<number> }) {
  const rimLightRef = useRef<THREE.SpotLight>(null)

  useFrame(() => {
    const p = progressRef.current ?? 0
    if (rimLightRef.current) {
      rimLightRef.current.intensity = 8.5 + Math.sin(p * Math.PI) * 2.5
    }
  })

  return (
    <>
      <ambientLight intensity={0.44} />

      {/* 1. Dramatic Warm Amber Backlight / Rim Light */}
      <spotLight
        ref={rimLightRef}
        position={[-4.5, 2.8, -2.5]}
        intensity={9.5}
        color="#ff8833"
        angle={0.7}
        penumbra={0.8}
        distance={15}
      />
      <pointLight position={[-3.2, 1.2, -1.0]} intensity={5.5} color="#ff7722" distance={8} />

      {/* 2. Crisp Key Light from Upper Right for Lens Barrel & Reflections */}
      <directionalLight position={[4.5, 5.0, 4.0]} intensity={4.2} color="#f0f5ff" />

      {/* 3. Soft Frontal Fill Light for Markings & Bezel Text */}
      <directionalLight position={[0.5, 1.5, 5.0]} intensity={2.0} color="#ffffff" />

      {/* 4. Top Overhead Studio Light */}
      <spotLight
        position={[0.5, 5.5, 0.5]}
        intensity={3.8}
        angle={0.55}
        penumbra={0.9}
        color="#e4ecf7"
      />

      {/* 5. Subtle Ground Bounce */}
      <pointLight position={[0.5, -1.5, 0.5]} intensity={2.0} color="#ff8844" distance={5} />
    </>
  )
}

// -------------------------------------------------------------
// TECHNICAL ANNOTATION COMPONENT
// -------------------------------------------------------------
function TechnicalAnnotation({
  x,
  y,
  title,
  subtitle,
  align = 'left',
}: {
  x: string
  y: string
  title: string
  subtitle: string
  align?: 'left' | 'right'
}) {
  return (
    <div
      className={`pointer-events-none absolute z-30 hidden sm:flex items-center gap-3 transition-all duration-700 ${
        align === 'right' ? 'flex-row-reverse text-right' : 'text-left'
      }`}
      style={{ left: x, top: y }}
    >
      <div className="relative flex size-3 items-center justify-center">
        <span className="size-1.5 rounded-full bg-white shadow-[0_0_8px_#ffffff]" />
        <span className="absolute size-3 animate-ping rounded-full bg-white/40" />
      </div>
      <div className="h-[1px] w-8 bg-gradient-to-r from-white/60 to-white/10" />
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[#f4f4f2]">
          {title}
        </p>
        <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-[#8c9096]">
          {subtitle}
        </p>
      </div>
    </div>
  )
}

// -------------------------------------------------------------
// MAIN CINEMATIC HERO COMPONENT
// -------------------------------------------------------------
export function CinematicHero({ onReady }: { onReady?: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const progressRef = useRef(0)
  const mouseRef = useRef({ x: 0, y: 0 })
  const [activeStage, setActiveStage] = useState(0)
  const [scrollProgress, setScrollProgress] = useState(0)

  // Track mouse movements for gentle parallax
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = {
        x: (e.clientX / window.innerWidth) * 2 - 1,
        y: (e.clientY / window.innerHeight) * 2 - 1,
      }
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    const trigger = ScrollTrigger.create({
      trigger: container,
      start: 'top top',
      end: 'bottom bottom',
      scrub: prefersReducedMotion ? 0 : 0.85,
      onUpdate: (self) => {
        const p = self.progress
        progressRef.current = p
        setScrollProgress(p)

        let stage = 0
        if (p < 0.20) stage = 0
        else if (p < 0.40) stage = 1
        else if (p < 0.60) stage = 2
        else if (p < 0.80) stage = 3
        else stage = 4

        setActiveStage(stage)
      },
    })

    return () => {
      trigger.kill()
    }
  }, [])

  const scrollToStage = (stageRatio: number) => {
    if (!containerRef.current) return
    const container = containerRef.current
    const top = container.offsetTop + stageRatio * (container.offsetHeight - window.innerHeight)
    window.scrollTo({ top, behavior: 'smooth' })
  }

  return (
    <div ref={containerRef} className="relative h-[600vh] w-full bg-[#040506]">
      {/* Sticky Fullscreen 3D Viewport */}
      <div className="sticky top-0 h-screen w-full overflow-hidden">
        {/* Dynamic Studio Gradient Backdrops without hard floor rings */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_38%_45%,rgba(255,120,40,0.065),transparent_50%),radial-gradient(circle_at_75%_55%,rgba(255,255,255,0.04),transparent_55%)]" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-[#040506]/90 via-transparent to-[#040506]" />

        {/* Subtle Fine Grid Texture */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage: `linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)`,
            backgroundSize: '96px 96px',
          }}
        />

        {/* Persistent 3D Canvas */}
        <div className="absolute inset-0 z-10">
          <Canvas
            camera={{ position: [0, 0.1, 5.2], fov: 40 }}
            dpr={[1, 2]}
            gl={{
              antialias: true,
              alpha: true,
              powerPreference: 'high-performance',
              toneMapping: THREE.ACESFilmicToneMapping,
              toneMappingExposure: 1.35,
            }}
          >
            <StudioLighting progressRef={progressRef} />
            <LensScene
              progressRef={progressRef}
              mouseRef={mouseRef}
              onReady={onReady}
            />
          </Canvas>
        </div>

        {/* Top-Left Category Badge */}
        <div className="pointer-events-none absolute left-6 top-24 z-20 hidden items-center gap-2.5 sm:flex lg:left-14 xl:left-16">
          <div className="size-2 rounded-full bg-[#00e599] shadow-[0_0_8px_#00e599]" />
          <span className="text-[10px] font-medium uppercase tracking-[0.24em] text-[#9a9ea4]">
            STUDIO 3D ARCHIVE // STAGE 0{activeStage + 1}
          </span>
        </div>

        {/* Right-Side Editorial 5-Stage Navigation */}
        <div className="pointer-events-auto absolute right-8 top-1/2 z-30 hidden -translate-y-1/2 flex-col items-end gap-3.5 lg:flex xl:right-14">
          <span className="mb-2 text-right text-[10px] font-semibold uppercase leading-tight tracking-[0.24em] text-[#c4c7cc]">
            EXPLORE
            <br />
            THE EXPERIENCE
          </span>

          {[
            { label: '01', title: 'Explore Every Detail', ratio: 0 },
            { label: '02', title: 'Precision in Every Frame', ratio: 0.25 },
            { label: '03', title: 'A Closer Perspective', ratio: 0.50 },
            { label: '04', title: 'Build Your Creator Kit', ratio: 0.75 },
            { label: '05', title: 'Your Next Story', ratio: 1.0 },
          ].map((item, idx) => (
            <button
              key={item.label}
              onClick={() => scrollToStage(item.ratio)}
              className="group flex items-center gap-3 py-1 text-right transition-all"
              title={item.title}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={`grid size-3.5 place-items-center rounded-full border transition-colors ${
                    activeStage === idx
                      ? 'border-white bg-transparent'
                      : 'border-white/30 group-hover:border-white/60'
                  }`}
                >
                  {activeStage === idx && <span className="size-1.5 rounded-full bg-white" />}
                </span>
                <span
                  className={`text-[11px] font-mono tracking-wider transition-colors ${
                    activeStage === idx
                      ? 'font-medium text-white'
                      : 'text-[#6b7076] group-hover:text-[#a0a5ab]'
                  }`}
                >
                  {item.label}
                </span>
              </div>
              <span
                className={`block h-[1px] transition-all duration-300 ${
                  activeStage === idx
                    ? 'w-7 bg-white'
                    : 'w-7 bg-white/20 group-hover:bg-white/40'
                }`}
              />
            </button>
          ))}
        </div>

        {/* Bottom Progress Bar */}
        <div className="pointer-events-none absolute bottom-0 left-0 right-0 z-30 h-[2px] bg-white/10">
          <div
            className="h-full bg-white transition-all duration-100 ease-out"
            style={{ width: `${scrollProgress * 100}%` }}
          />
        </div>

        {/* ------------------------------------------------------------- */}
        {/* INITIAL HERO (STAGE 00) — SOME MOMENTS DESERVE MORE           */}
        {/* ------------------------------------------------------------- */}
        <div
          className={`pointer-events-none absolute inset-0 z-20 flex flex-col justify-center px-6 transition-all duration-700 sm:px-10 lg:px-14 xl:px-16 ${
            activeStage === 0
              ? 'opacity-100 translate-y-0'
              : 'opacity-0 -translate-y-8 pointer-events-none'
          }`}
        >
          <div className="mx-auto grid w-full max-w-[1780px] grid-cols-1 items-center md:grid-cols-[1.05fr_0.95fr]">
            <div className="pointer-events-auto max-w-[640px]">
              {/* Requested Editorial Headline */}
              <h1 className="font-heading text-[clamp(48px,6.8vw,96px)] font-semibold leading-[0.94] tracking-[-0.04em] text-[#f4f4f2]">
                Some Moments
                <br />
                <span className="text-[#888c91]">Deserve</span>
                <br />
                More.
              </h1>

              {/* Exact Requested Supporting Copy */}
              <p className="mt-7 max-w-[500px] text-base font-normal leading-[1.65] text-[#9ea2a6] lg:text-lg lg:leading-[1.7]">
                From the first frame to the final cut, access the equipment that brings your creative vision to life.
              </p>

              {/* Buttons: Explore Equipment & Build Your Creator Kit */}
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <a
                  href="#gear"
                  className="group inline-flex items-center gap-3 rounded-none border border-white bg-white px-8 py-4 text-xs font-semibold uppercase tracking-[0.16em] text-[#050607] transition-all duration-300 hover:bg-[#e4e5e7] hover:shadow-[0_0_30px_rgba(255,255,255,0.25)]"
                >
                  <span>EXPLORE EQUIPMENT</span>
                  <ArrowRight className="size-3.5 transition-transform duration-300 group-hover:translate-x-1" />
                </a>

                <a
                  href="#kits"
                  className="inline-flex items-center gap-2 rounded-none border border-white/20 bg-transparent px-8 py-4 text-xs font-medium uppercase tracking-[0.16em] text-[#f4f4f2] transition-all duration-300 hover:border-white/50 hover:bg-white/[0.04]"
                >
                  <span>BUILD YOUR CREATOR KIT</span>
                </a>
              </div>

              {/* Editorial Trust Specs */}
              <div className="mt-12 flex flex-wrap items-center gap-x-8 gap-y-3 pt-4 text-[10px] font-medium tracking-[0.12em] text-[#b0b4ba]">
                <span className="flex items-center gap-2">
                  <Aperture className="size-4 stroke-[1.75] text-[#d0d3d8]" />
                  Cine Optics
                </span>
                <span className="flex items-center gap-2">
                  <LayersIcon className="size-4 stroke-[1.75] text-[#d0d3d8]" />
                  Multi-Coated Elements
                </span>
                <span className="flex items-center gap-2">
                  <ShieldCheck className="size-4 stroke-[1.75] text-[#d0d3d8]" />
                  Zero Deposit Options
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* STAGE 01 — EXPLORE EVERY DETAIL                               */}
        {/* ------------------------------------------------------------- */}
        <div
          className={`pointer-events-none absolute inset-0 z-20 flex flex-col justify-center px-6 transition-all duration-700 sm:px-10 lg:px-14 xl:px-16 ${
            activeStage === 1
              ? 'opacity-100 translate-y-0'
              : 'opacity-0 translate-y-8 pointer-events-none'
          }`}
        >
          <div className="mx-auto flex w-full max-w-[1780px] flex-col items-start">
            <div className="pointer-events-auto max-w-[560px]">
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.26em] text-[#8c9094]">
                <Focus className="size-3.5 text-white/80" />
                <span>STAGE 01 // CONTROLLED PUSH-IN</span>
              </div>

              <h2 className="font-heading mt-4 text-[clamp(36px,5.2vw,70px)] font-medium leading-[0.98] tracking-[-0.04em] text-[#f4f4f2]">
                Explore Every
                <br />
                <span className="text-[#888c91]">Detail.</span>
              </h2>

              <p className="mt-5 max-w-[480px] text-base font-normal leading-[1.65] text-[#9ea2a6]">
                Controlled camera movement reveals the precision machining of the lens barrel, engraved tactile focus scales, and anti-reflective optical coatings.
              </p>

              <div className="mt-8 grid grid-cols-2 gap-4 border-t border-white/10 pt-6">
                <div>
                  <span className="font-mono text-[9px] uppercase tracking-[0.24em] text-[#73767a]">Optic Element</span>
                  <p className="mt-1 font-heading text-lg font-medium text-white">Fluorite & ED Glass</p>
                </div>
                <div>
                  <span className="font-mono text-[9px] uppercase tracking-[0.24em] text-[#73767a]">Barrel Chassis</span>
                  <p className="mt-1 font-heading text-lg font-medium text-white">All-Weather Magnesium</p>
                </div>
              </div>
            </div>
          </div>

          {/* Technical Annotations over 3D model */}
          {activeStage === 1 && (
            <>
              <TechnicalAnnotation
                x="56%"
                y="34%"
                title="Nano Coating"
                subtitle="Anti-Reflective Layer"
                align="right"
              />
              <TechnicalAnnotation
                x="64%"
                y="66%"
                title="USM Motor"
                subtitle="Silent High-Speed Ring"
                align="left"
              />
            </>
          )}
        </div>

        {/* ------------------------------------------------------------- */}
        {/* STAGE 02 — PRECISION IN EVERY FRAME                           */}
        {/* ------------------------------------------------------------- */}
        <div
          className={`pointer-events-none absolute inset-0 z-20 flex flex-col justify-center px-6 transition-all duration-700 sm:px-10 lg:px-14 xl:px-16 ${
            activeStage === 2
              ? 'opacity-100 translate-y-0'
              : 'opacity-0 translate-y-8 pointer-events-none'
          }`}
        >
          <div className="mx-auto flex w-full max-w-[1780px] justify-start">
            <div className="pointer-events-auto max-w-[560px]">
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.26em] text-[#8c9094]">
                <Layers className="size-3.5 text-white/80" />
                <span>STAGE 02 // 180° ROTATION</span>
              </div>

              <h2 className="font-heading mt-4 text-[clamp(36px,5.2vw,70px)] font-medium leading-[0.98] tracking-[-0.04em] text-[#f4f4f2]">
                Precision in
                <br />
                <span className="text-[#888c91]">Every Frame.</span>
              </h2>

              <p className="mt-5 max-w-[480px] text-base font-normal leading-[1.65] text-[#9ea2a6]">
                A continuous 180-degree sweep unveils the electronic bayonet mount, weather-sealing gaskets, and smooth mechanical gearing designed for seamless cinematography.
              </p>

              <div className="mt-8 grid grid-cols-2 gap-4 border-t border-white/10 pt-6">
                <div>
                  <span className="font-mono text-[9px] uppercase tracking-[0.24em] text-[#73767a]">Mount Interface</span>
                  <p className="mt-1 font-heading text-lg font-medium text-white">Active Electronic Flange</p>
                </div>
                <div>
                  <span className="font-mono text-[9px] uppercase tracking-[0.24em] text-[#73767a]">Iris Design</span>
                  <p className="mt-1 font-heading text-lg font-medium text-white">9-Blade Circular Aperture</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* STAGE 03 — A CLOSER PERSPECTIVE / PROFESSIONAL GEAR            */}
        {/* ------------------------------------------------------------- */}
        <div
          className={`pointer-events-none absolute inset-0 z-20 flex flex-col justify-center px-6 transition-all duration-700 sm:px-10 lg:px-14 xl:px-16 ${
            activeStage === 3
              ? 'opacity-100 translate-y-0'
              : 'opacity-0 translate-y-8 pointer-events-none'
          }`}
        >
          <div className="mx-auto flex w-full max-w-[1780px] justify-start lg:justify-end">
            <div className="pointer-events-auto max-w-[560px]">
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.26em] text-[#8c9094]">
                <Aperture className="size-3.5 text-white/80" />
                <span>STAGE 03 // MACRO PERSPECTIVE</span>
              </div>

              <h2 className="font-heading mt-4 text-[clamp(36px,5.2vw,70px)] font-medium leading-[0.98] tracking-[-0.04em] text-[#f4f4f2]">
                Professional Gear.
                <br />
                <span className="text-[#888c91]">Zero Ownership.</span>
              </h2>

              <p className="mt-5 max-w-[480px] text-base font-normal leading-[1.65] text-[#9ea2a6]">
                Experience high-end cinematic optics with zero capital commitment. Access industry-standard glass inspected and calibrated before every production.
              </p>

              <div className="mt-8 grid grid-cols-2 gap-3 border-t border-white/10 pt-6">
                <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-white/90">
                  <ShieldCheck className="size-3.5 text-white/60" />
                  <span>Insured Rentals</span>
                </div>
                <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-white/90">
                  <Check className="size-3.5 text-white/60" />
                  <span>Doorstep Delivery</span>
                </div>
                <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-white/90">
                  <Aperture className="size-3.5 text-white/60" />
                  <span>Zero Deposit Options</span>
                </div>
                <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-white/90">
                  <Focus className="size-3.5 text-white/60" />
                  <span>100% Calibrated</span>
                </div>
              </div>
            </div>
          </div>

          {activeStage === 3 && (
            <TechnicalAnnotation
              x="32%"
              y="38%"
              title="Multi-Coated Glass"
              subtitle="Zero Aberration Transmission"
              align="right"
            />
          )}
        </div>

        {/* ------------------------------------------------------------- */}
        {/* STAGE 04 & 05 — BUILD YOUR CREATOR KIT / YOUR NEXT STORY       */}
        {/* ------------------------------------------------------------- */}
        <div
          className={`pointer-events-none absolute inset-0 z-20 flex flex-col justify-center px-6 transition-all duration-700 sm:px-10 lg:px-14 xl:px-16 ${
            activeStage === 4
              ? 'opacity-100 translate-y-0'
              : 'opacity-0 translate-y-8 pointer-events-none'
          }`}
        >
          <div className="mx-auto flex w-full max-w-[1780px] flex-col items-start lg:items-start">
            <div className="pointer-events-auto max-w-[640px]">
              <div className="inline-flex items-center gap-2 border border-white/20 bg-white/[0.04] px-4 py-1.5 text-[10px] font-medium uppercase tracking-[0.26em] text-[#c5c8cc]">
                <Sparkles className="size-3.5 text-white" />
                <span>STAGE 04 & 05 // PRODUCTION READY</span>
              </div>

              {/* Headlines */}
              <h2 className="font-heading mt-6 text-[clamp(40px,5.8vw,80px)] font-medium leading-[0.96] tracking-[-0.045em] text-[#f4f4f2]">
                Your Next Story
                <br />
                <span className="text-[#888c91]">Starts Here.</span>
              </h2>

              <p className="mt-5 max-w-[520px] text-base font-normal leading-[1.65] text-[#9ea2a6] sm:text-lg">
                Pair precision optics with cinema camera bodies, wireless audio, and essential rigging. Everything you need in one complete kit.
              </p>

              {/* Exact User Buttons */}
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <a
                  href="#gear"
                  className="group inline-flex items-center gap-3 border border-white bg-[#f4f4f2] px-8 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-[#050607] transition-all duration-300 hover:bg-white hover:shadow-[0_0_40px_rgba(255,255,255,0.25)] hover:scale-105"
                >
                  <span>EXPLORE EQUIPMENT</span>
                  <ArrowRight className="size-3.5 transition-transform duration-300 group-hover:translate-x-1" />
                </a>

                <a
                  href="#kits"
                  className="inline-flex items-center gap-2 border border-white/30 bg-white/[0.05] px-8 py-4 text-xs font-medium uppercase tracking-[0.18em] text-[#f4f4f2] transition-all duration-300 hover:border-white hover:bg-white/[0.12] hover:scale-105"
                >
                  <Package className="size-3.5 text-white/80" />
                  <span>BUILD YOUR CREATOR KIT</span>
                </a>
              </div>

              {/* Equipment composition preview link */}
              <div className="mt-8 flex items-center gap-4 border-t border-white/10 pt-5 text-[10px] uppercase tracking-[0.2em] text-[#808488]">
                <span className="flex items-center gap-1.5">
                  <Shield className="size-3.5 text-white/70" />
                  Insured Rentals
                </span>
                <span className="flex items-center gap-1.5">
                  <Camera className="size-3.5 text-white/70" />
                  Cinema Systems
                </span>
                <span className="flex items-center gap-1.5">
                  <Sparkles className="size-3.5 text-white/70" />
                  Fast Turnaround
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom "SCROLL TO EXPLORE" Prompt */}
        <div className="pointer-events-none absolute bottom-5 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 text-[9px] uppercase tracking-[0.22em] text-[#787d84]">
          <span className="flex items-center gap-1">
            SCROLL TO EXPLORE THE 3D EXPERIENCE
            <ChevronDown className="size-3 text-[#787d84]" />
          </span>
          <ChevronDown className="size-3.5 animate-bounce text-[#a0a5ab]" />
        </div>
      </div>
    </div>
  )
}
