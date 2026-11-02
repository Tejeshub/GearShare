export interface Product {
  id: string
  name: string
  brand: string
  category: 'Cameras' | 'Lenses' | 'Lighting' | 'Stabilization' | 'Car Mount' | 'Camera Strap' | 'Tripod' | 'Gimbal'
  description: string
  image: string
  spec: string
  specs: string[]
  price: number // daily rental price in INR (₹)
  availability: 'Available' | 'Low Stock' | 'Reserved'
}

// Exactly the eight finalized catalog products specified for the calculator
export const calculatorProducts: Product[] = [
  // Cameras
  {
    id: 'sony-fx30',
    name: 'Sony FX30',
    brand: 'Sony',
    category: 'Cameras',
    description: 'Cinema Line Super 35 camera designed for visionary filmmakers. Features dual base ISO, 4K 120p recording, and professional 10-bit 4:2:2 color profiles.',
    image: '/images/products/sony-fx30.jpg',
    spec: 'Cinema Super 35 · 4K 120p · Dual Base ISO',
    specs: ['Super 35mm Exmor R CMOS Sensor', '4K up to 120fps / FHD 240fps', 'Dual Base ISO (800 / 2500)', 'S-Cinetone, S-Log3, HLG'],
    price: 3499,
    availability: 'Available',
  },
  {
    id: 'sony-a7-iv',
    name: 'Sony A7 IV',
    brand: 'Sony',
    category: 'Cameras',
    description: 'The ultimate hybrid full-frame camera. Delivering 33MP high-resolution stills alongside 4K 60p 10-bit video with state-of-the-art real-time autofocus.',
    image: '/images/products/sony-a7-iv.jpg',
    spec: '33MP Full-Frame · 4K 60p · 10-bit 4:2:2',
    specs: ['33MP Full-Frame Exmor R Sensor', 'BIONZ XR Image Processor', '759-point Phase-detection AF', '5-axis Optical In-body Stabilization'],
    price: 2999,
    availability: 'Available',
  },
  {
    id: 'canon-eos-r6-ii',
    name: 'Canon EOS R6 Mark II',
    brand: 'Canon',
    category: 'Cameras',
    description: 'Speed, low-light precision, and unmatched hybrid filmmaking performance. Shoots 40fps electronic shutter and oversampled 6K-to-4K 60p without crop.',
    image: '/images/products/canon-eos-r6-ii.jpg',
    spec: '24.2MP CMOS · 40fps · 6K Oversampled 4K',
    specs: ['24.2MP Full-Frame CMOS Sensor', '4K 60p 10-bit internal recording', 'Up to 8-stop In-Body IS', 'Dual Pixel CMOS AF II with Deep Learning'],
    price: 3199,
    availability: 'Available',
  },
  {
    id: 'nikon-z8',
    name: 'Nikon Z8',
    brand: 'Nikon',
    category: 'Cameras',
    description: 'Flagship Z9 capabilities packed into a compact, agile body. 45.7MP stacked sensor, blackout-free real-time viewfinder, and internal 8.3K 60p N-RAW recording.',
    image: '/images/products/nikon-z8.jpg',
    spec: '45.7MP Stacked · 8.3K 60p RAW · Blackout-Free',
    specs: ['45.7MP Stacked CMOS Sensor', 'Internal 8.3K 60p N-RAW & ProRes RAW', 'Completely Electronic Shutter', 'Subject Detection with 9 Subject Types'],
    price: 4499,
    availability: 'Available',
  },

  // Lenses
  {
    id: 'sony-24-70-gm2',
    name: 'Sony FE 24–70mm F2.8 GM II',
    brand: 'Sony',
    category: 'Lenses',
    description: 'The world’s lightest and sharpest fast standard zoom. E-mount optical pinnacle with four XD linear motors, reduced focus breathing, and f/2.8 constant aperture.',
    image: '/images/products/sony-24-70-gm2.jpg',
    spec: 'f/2.8 Constant · G Master · Four XD Linear Motors',
    specs: ['Focal Length: 24–70mm', 'Maximum Aperture: f/2.8 Constant', 'Nano AR Coating II', 'Filter Diameter: 82mm'],
    price: 1899,
    availability: 'Available',
  },
  {
    id: 'sony-70-200-gm2',
    name: 'Sony FE 70–200mm F2.8 GM II',
    brand: 'Sony',
    category: 'Lenses',
    description: 'Flagship telephoto zoom delivering unprecedented resolution, contrast, and autofocus tracking speed in an ultra-lightweight chassis.',
    image: '/images/products/sony-70-200-gm2.jpg',
    spec: 'f/2.8 Constant · Telephoto G Master · Dual Linear Motors',
    specs: ['Focal Length: 70–200mm', 'Maximum Aperture: f/2.8 Constant', 'Optical SteadyShot Stabilization', 'Filter Diameter: 77mm'],
    price: 2499,
    availability: 'Available',
  },

  // Lighting
  {
    id: 'aputure-300d-ii',
    name: 'Aputure 300D II',
    brand: 'Aputure',
    category: 'Lighting',
    description: 'Industry-standard 5500K daylight point-source LED fixture. Generates exceptional 96+ CRI punch with Bowens mount light shapers and wireless Sidus Link control.',
    image: '/images/products/aputure-300d-ii.jpg',
    spec: '5500K Daylight · Bowens Mount · 96+ CRI / TLCI',
    specs: ['300W COB LED Output', '5500K Daylight Balanced', 'CRI 96+ / TLCI 97+', 'Active Silent Fan Cooling'],
    price: 1999,
    availability: 'Available',
  },

  // Stabilization
  {
    id: 'dji-rs4-pro',
    name: 'DJI RS 4 Pro',
    brand: 'DJI',
    category: 'Stabilization',
    description: 'Next-gen flagship commercial camera stabilizer. Second-generation automated axis locks, native vertical shooting, 4.5kg payload capacity, and LiDAR autofocus integration.',
    image: '/images/products/dji-rs4-pro.jpg',
    spec: 'Automated Locks · 4.5kg Payload · LiDAR Ready',
    specs: ['Carbon Fiber Arms with Teflon Coating', 'Second-Generation Automated Axis Locks', '4.5kg (10 lbs) Tested Payload', 'Native 2nd Gen Vertical Shooting'],
    price: 2299,
    availability: 'Available',
  },
]

// All finalized catalog products for Section 02 / Featured Equipment
export const finalizedProducts: Product[] = [
  // 1. Cameras
  {
    id: 'sony-fx30',
    name: 'Sony FX30',
    brand: 'Sony',
    category: 'Cameras',
    description: 'Cinema Line Super 35 camera designed for visionary filmmakers. Features dual base ISO, 4K 120p recording, and professional 10-bit 4:2:2 color profiles.',
    image: '/images/products/sony-fx30.jpg',
    spec: 'Cinema Super 35 · 4K 120p · Dual Base ISO',
    specs: ['Super 35mm Exmor R CMOS Sensor', '4K up to 120fps / FHD 240fps', 'Dual Base ISO (800 / 2500)', 'S-Cinetone, S-Log3, HLG'],
    price: 3499,
    availability: 'Available',
  },
  {
    id: 'canon-eos-r6-ii',
    name: 'Canon EOS R6 Mark II',
    brand: 'Canon',
    category: 'Cameras',
    description: 'Speed, low-light precision, and unmatched hybrid filmmaking performance. Shoots 40fps electronic shutter and oversampled 6K-to-4K 60p without crop.',
    image: '/images/products/canon-eos-r6-ii.jpg',
    spec: '24.2MP CMOS · 40fps · 6K Oversampled 4K',
    specs: ['24.2MP Full-Frame CMOS Sensor', '4K 60p 10-bit internal recording', 'Up to 8-stop In-Body IS', 'Dual Pixel CMOS AF II with Deep Learning'],
    price: 3199,
    availability: 'Available',
  },
  {
    id: 'nikon-z8',
    name: 'Nikon Z8',
    brand: 'Nikon',
    category: 'Cameras',
    description: 'Flagship Z9 capabilities packed into a compact, agile body. 45.7MP stacked sensor, blackout-free real-time viewfinder, and internal 8.3K 60p N-RAW recording.',
    image: '/images/products/nikon-z8.jpg',
    spec: '45.7MP Stacked · 8.3K 60p RAW · Blackout-Free',
    specs: ['45.7MP Stacked CMOS Sensor', 'Internal 8.3K 60p N-RAW & ProRes RAW', 'Completely Electronic Shutter', 'Subject Detection with 9 Subject Types'],
    price: 4499,
    availability: 'Available',
  },

  // 2. Lenses
  {
    id: 'sony-24-70-gm2',
    name: 'Sony FE 24–70mm F2.8 GM II',
    brand: 'Sony',
    category: 'Lenses',
    description: 'The world’s lightest and sharpest fast standard zoom. E-mount optical pinnacle with four XD linear motors, reduced focus breathing, and f/2.8 constant aperture.',
    image: '/images/products/sony-24-70-gm2.jpg',
    spec: 'f/2.8 Constant · G Master · Four XD Linear Motors',
    specs: ['Focal Length: 24–70mm', 'Maximum Aperture: f/2.8 Constant', 'Nano AR Coating II', 'Filter Diameter: 82mm'],
    price: 1899,
    availability: 'Available',
  },

  // 3. Car Mount
  {
    id: 'suction-car-mount-pro',
    name: 'Suction Car Mount Pro',
    brand: 'Tilta',
    category: 'Car Mount',
    description: 'Professional high-speed suction car mounting system engineered for cameras and gimbals. Features pneumatic vacuum suction cups with hydraulic damping shock-absorbing arm.',
    image: '/images/products/suction-car-mount-pro.png',
    spec: 'Hydraulic Damping · 4.5kg Payload · High-Speed Vacuum',
    specs: ['Tri-cup Pneumatic Vacuum System', 'Hydraulic Damping Shock Absorber', 'Rated for Speeds up to 100 km/h', 'Quick-Release 1/4" and 3/8" Studs'],
    price: 1499,
    availability: 'Available',
  },

  // 4. Camera Strap
  {
    id: 'vintage-camera-strap',
    name: 'Vintage Embroidered Camera Strap',
    brand: 'Artisan',
    category: 'Camera Strap',
    description: 'Handcrafted jacquard woven vintage camera neck and shoulder strap with genuine reinforced leather ends and high-tensile quick-release buckles.',
    image: '/images/products/vintage-camera-strap.jpg',
    spec: 'Jacquard Weave · Leather Ends · Quick Release',
    specs: ['Wide Ergonomic Breathable Weave', 'Reinforced Full-Grain Leather Ends', 'Universal Quick-Release Mounts', 'Adjustable 90cm to 135cm Length'],
    price: 399,
    availability: 'Available',
  },

  // 5. Tripod
  {
    id: 'ulanzi-carbon-tripod',
    name: 'Carbon Travel Tripod with Prompter Rig',
    brand: 'Ulanzi',
    category: 'Tripod',
    description: 'Ultra-lightweight multi-section carbon fiber video and photo tripod equipped with fluid panoramic ball head, phone/teleprompter display bracket, and Arca-Swiss mount.',
    image: '/images/products/ulanzi-carbon-tripod.png',
    spec: 'Carbon Fibre · Teleprompter Rig · Arca-Swiss Head',
    specs: ['High-Strength 8-Layer Carbon Fiber', 'Dual Panoramic Ball Head', 'Integrated Teleprompter/Monitor Mount', 'Max Height 160cm · Folded 38cm'],
    price: 799,
    availability: 'Available',
  },

  // 6. Gimbal
  {
    id: 'dji-rs3-pro',
    name: 'DJI RS3 Pro Gimbal',
    brand: 'DJI',
    category: 'Gimbal',
    description: 'Automated 3-axis motorized camera stabilizer with extended carbon fiber axis arms, vertical shooting mount, 4.5kg tested payload, and SuperSmooth algorithm.',
    image: '/images/products/dji-rs3-pro.png',
    spec: '3-Axis Motorized · Vertical Mount · 4.5kg Payload',
    specs: ['Carbon Fiber Construction', 'Automated Axis Locks', 'Native Vertical Shooting Plate for RS3', 'LiDAR Autofocus Compatibility'],
    price: 1899,
    availability: 'Available',
  },
]

// Centralized Creator Kits connected to product catalog
export interface CreatorKit {
  id: string
  title: string
  tag: string
  intendedUse: string
  description: string
  image: string
  price: number // Combined daily rental price in INR
  productIds: string[]
  includedItems: Array<{ role: string; name: string }>
}

export const creatorKits: CreatorKit[] = [
  {
    id: 'insta360-luna-ultra',
    title: 'Insta360 Luna Ultra Creator Bundle',
    tag: 'ULTRA 360 / IMMERSIVE',
    intendedUse: 'Next-generation 8K 360° capture, interactive virtual tours, high-motion vlogging, and dual-lens creative storytelling.',
    description: 'The all-in-one handheld dual-lens ultra creator bundle. Features dual Leica optics, integrated touchscreen monitor, wireless audio receiver, magnetic battery modules, and protective travel case.',
    image: '/images/kits/insta360-luna-ultra.png',
    price: 3899,
    productIds: ['dji-rs3-pro', 'vintage-camera-strap'],
    includedItems: [
      { role: 'Dual-Lens Camera', name: 'Insta360 Dual-Lens 8K Master Body' },
      { role: 'Monitoring & Control', name: 'Flip Touchscreen Display & Smart Grip' },
      { role: 'Audio & Wireless', name: 'Snap-On Wireless Mic Transmitter & Receiver' },
      { role: 'Power & Storage', name: 'Dual Expansion Battery Packs & Protective Case' },
    ],
  },
  {
    id: 'content-creator-kit',
    title: 'Content Creator Kit',
    tag: 'STREAMING / WORKSPACE',
    intendedUse: 'Professional YouTube studio setups, live streaming, desktop b-roll production, and high-engagement content workflows.',
    description: 'The ultimate desktop and studio workstation setup. Complete with hybrid camera body, bi-color ring light with smartphone/camera mount, shotgun audio, tabletop flex tripod, and monitoring interface.',
    image: '/images/kits/content-creator-kit.png',
    price: 4999,
    productIds: ['sony-fx30', 'sony-24-70-gm2', 'ulanzi-carbon-tripod'],
    includedItems: [
      { role: 'Production Camera', name: 'Sony FX30 Cinema Hybrid' },
      { role: 'Lighting Ring', name: 'Bi-Color Studio Ring Light with Stand' },
      { role: 'Support & Mount', name: 'Flexible Articulating GorillaPod & Phone Mount' },
      { role: 'Audio & Power', name: 'On-Camera Shotgun Mic & USB-C Power Rig' },
    ],
  },
  {
    id: 'canon-content-creator',
    title: 'Canon Content Creator Kit',
    tag: 'CREATOR / HYBRID',
    intendedUse: 'Vlogging, run-and-gun documentary, travel filmmaking, and Decisive Moment photo & 4K video storytelling.',
    description: 'Official Canon Creator Pack centered on the compact EOS R50 / R6 mirrorless platform. Bundled with the versatile RF-S zoom lens, Canon HG-100TBR tripod grip with wireless remote, and directional stereo microphone with deadcat windscreen.',
    image: '/images/kits/canon-content-creator.png',
    price: 4299,
    productIds: ['canon-eos-r6-ii', 'ulanzi-carbon-tripod', 'vintage-camera-strap'],
    includedItems: [
      { role: 'Mirrorless Camera', name: 'Canon EOS Mirrorless Body (4K Uncropped)' },
      { role: 'Standard Zoom Lens', name: 'Canon RF-S 18–45mm f/4.5–6.3 IS STM' },
      { role: 'Tripod Grip', name: 'Canon HG-100TBR Wireless Remote Tripod Grip' },
      { role: 'Directional Audio', name: 'Canon DM-E100 Stereo Microphone with Deadcat' },
    ],
  },
]
