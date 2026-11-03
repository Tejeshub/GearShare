import logging
from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.catalog import (
    AvailabilityStatus,
    Category,
    CreatorKit,
    CreatorKitItem,
    Equipment,
)

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Exact 8 Categories required by frontend combined catalogue
# -------------------------------------------------------------------------
CATEGORIES_SEED_DATA: List[Dict[str, Any]] = [
    {
        "name": "Cameras",
        "slug": "cameras",
        "description": "Bodies built for decisive moments.",
        "sort_order": 1,
        "is_visible_in_category_section": True,
    },
    {
        "name": "Lenses",
        "slug": "lenses",
        "description": "Glass that changes perspective.",
        "sort_order": 2,
        "is_visible_in_category_section": True,
    },
    {
        "name": "Lighting",
        "slug": "lighting",
        "description": "Point-source, softbox, and bi-color studio illuminators.",
        "sort_order": 3,
        "is_visible_in_category_section": False,  # Not in 6-card homepage grid, used in calculator
    },
    {
        "name": "Stabilization",
        "slug": "stabilization",
        "description": "Flagship gimbals and mechanical steady mounts.",
        "sort_order": 4,
        "is_visible_in_category_section": False,  # Used in calculator
    },
    {
        "name": "Car Mount",
        "slug": "car-mount",
        "description": "High-speed dynamic vehicle rigs.",
        "sort_order": 5,
        "is_visible_in_category_section": True,
    },
    {
        "name": "Camera Strap",
        "slug": "camera-strap",
        "description": "Ergonomic woven and leather straps.",
        "sort_order": 6,
        "is_visible_in_category_section": True,
    },
    {
        "name": "Tripod",
        "slug": "tripod",
        "description": "Rock-solid support for every frame.",
        "sort_order": 7,
        "is_visible_in_category_section": True,
    },
    {
        "name": "Gimbal",
        "slug": "gimbal",
        "description": "Precision 3-axis motorized motion.",
        "sort_order": 8,
        "is_visible_in_category_section": True,
    },
]

# -------------------------------------------------------------------------
# Exact 12 Unique Equipment Products from combined frontend collections
# -------------------------------------------------------------------------
EQUIPMENT_SEED_DATA: List[Dict[str, Any]] = [
    {
        "id": "sony-fx30",
        "name": "Sony FX30",
        "brand": "Sony",
        "category_slug": "cameras",
        "description": "Cinema Line Super 35 camera designed for visionary filmmakers. Features dual base ISO, 4K 120p recording, and professional 10-bit 4:2:2 color profiles.",
        "image": "/images/products/sony-fx30.webp",
        "spec": "Cinema Super 35 · 4K 120p · Dual Base ISO",
        "specs": [
            "Super 35mm Exmor R CMOS Sensor",
            "4K up to 120fps / FHD 240fps",
            "Dual Base ISO (800 / 2500)",
            "S-Cinetone, S-Log3, HLG",
        ],
        "price": Decimal("3499.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
    {
        "id": "sony-a7-iv",
        "name": "Sony A7 IV",
        "brand": "Sony",
        "category_slug": "cameras",
        "description": "The ultimate hybrid full-frame camera. Delivering 33MP high-resolution stills alongside 4K 60p 10-bit video with state-of-the-art real-time autofocus.",
        "image": "/images/products/sony-a7-iv.webp",
        "spec": "33MP Full-Frame · 4K 60p · 10-bit 4:2:2",
        "specs": [
            "33MP Full-Frame Exmor R Sensor",
            "BIONZ XR Image Processor",
            "759-point Phase-detection AF",
            "5-axis Optical In-body Stabilization",
        ],
        "price": Decimal("2999.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": False,
        "is_rentable": True,
    },
    {
        "id": "canon-eos-r6-ii",
        "name": "Canon EOS R6 Mark II",
        "brand": "Canon",
        "category_slug": "cameras",
        "description": "Speed, low-light precision, and unmatched hybrid filmmaking performance. Shoots 40fps electronic shutter and oversampled 6K-to-4K 60p without crop.",
        "image": "/images/products/canon-eos-r6-ii.webp",
        "spec": "24.2MP CMOS · 40fps · 6K Oversampled 4K",
        "specs": [
            "24.2MP Full-Frame CMOS Sensor",
            "4K 60p 10-bit internal recording",
            "Up to 8-stop In-Body IS",
            "Dual Pixel CMOS AF II with Deep Learning",
        ],
        "price": Decimal("3199.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
    {
        "id": "nikon-z8",
        "name": "Nikon Z8",
        "brand": "Nikon",
        "category_slug": "cameras",
        "description": "Flagship Z9 capabilities packed into a compact, agile body. 45.7MP stacked sensor, blackout-free real-time viewfinder, and internal 8.3K 60p N-RAW recording.",
        "image": "/images/products/nikon-z8.webp",
        "spec": "45.7MP Stacked · 8.3K 60p RAW · Blackout-Free",
        "specs": [
            "45.7MP Stacked CMOS Sensor",
            "Internal 8.3K 60p N-RAW & ProRes RAW",
            "Completely Electronic Shutter",
            "Subject Detection with 9 Subject Types",
        ],
        "price": Decimal("4499.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
    {
        "id": "sony-24-70-gm2",
        "name": "Sony FE 24–70mm F2.8 GM II",
        "brand": "Sony",
        "category_slug": "lenses",
        "description": "The world’s lightest and sharpest fast standard zoom. E-mount optical pinnacle with four XD linear motors, reduced focus breathing, and f/2.8 constant aperture.",
        "image": "/images/products/sony-24-70-gm2.webp",
        "spec": "f/2.8 Constant · G Master · Four XD Linear Motors",
        "specs": [
            "Focal Length: 24–70mm",
            "Maximum Aperture: f/2.8 Constant",
            "Nano AR Coating II",
            "Filter Diameter: 82mm",
        ],
        "price": Decimal("1899.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
    {
        "id": "sony-70-200-gm2",
        "name": "Sony FE 70–200mm F2.8 GM II",
        "brand": "Sony",
        "category_slug": "lenses",
        "description": "Flagship telephoto zoom delivering unprecedented resolution, contrast, and autofocus tracking speed in an ultra-lightweight chassis.",
        "image": "/images/products/sony-70-200-gm2.webp",
        "spec": "f/2.8 Constant · Telephoto G Master · Dual Linear Motors",
        "specs": [
            "Focal Length: 70–200mm",
            "Maximum Aperture: f/2.8 Constant",
            "Optical SteadyShot Stabilization",
            "Filter Diameter: 77mm",
        ],
        "price": Decimal("2499.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": False,
        "is_rentable": True,
    },
    {
        "id": "aputure-300d-ii",
        "name": "Aputure 300D II",
        "brand": "Aputure",
        "category_slug": "lighting",
        "description": "Industry-standard 5500K daylight point-source LED fixture. Generates exceptional 96+ CRI punch with Bowens mount light shapers and wireless Sidus Link control.",
        "image": "/images/products/aputure-300d-ii.webp",
        "spec": "5500K Daylight · Bowens Mount · 96+ CRI / TLCI",
        "specs": [
            "300W COB LED Output",
            "5500K Daylight Balanced",
            "CRI 96+ / TLCI 97+",
            "Active Silent Fan Cooling",
        ],
        "price": Decimal("1999.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": False,
        "is_rentable": True,
    },
    {
        "id": "dji-rs4-pro",
        "name": "DJI RS 4 Pro",
        "brand": "DJI",
        "category_slug": "stabilization",
        "description": "Next-gen flagship commercial camera stabilizer. Second-generation automated axis locks, native vertical shooting, 4.5kg payload capacity, and LiDAR autofocus integration.",
        "image": "/images/products/dji-rs4-pro.webp",
        "spec": "Automated Locks · 4.5kg Payload · LiDAR Ready",
        "specs": [
            "Carbon Fiber Arms with Teflon Coating",
            "Second-Generation Automated Axis Locks",
            "4.5kg (10 lbs) Tested Payload",
            "Native 2nd Gen Vertical Shooting",
        ],
        "price": Decimal("2299.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": False,
        "is_rentable": True,
    },
    {
        "id": "suction-car-mount-pro",
        "name": "Suction Car Mount Pro",
        "brand": "Tilta",
        "category_slug": "car-mount",
        "description": "Professional high-speed suction car mounting system engineered for cameras and gimbals. Features pneumatic vacuum suction cups with hydraulic damping shock-absorbing arm.",
        "image": "/images/products/suction-car-mount-pro.webp",
        "spec": "Hydraulic Damping · 4.5kg Payload · High-Speed Vacuum",
        "specs": [
            "Tri-cup Pneumatic Vacuum System",
            "Hydraulic Damping Shock Absorber",
            "Rated for Speeds up to 100 km/h",
            "Quick-Release 1/4\" and 3/8\" Studs",
        ],
        "price": Decimal("1499.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
    {
        "id": "vintage-camera-strap",
        "name": "Vintage Embroidered Camera Strap",
        "brand": "Artisan",
        "category_slug": "camera-strap",
        "description": "Handcrafted jacquard woven vintage camera neck and shoulder strap with genuine reinforced leather ends and high-tensile quick-release buckles.",
        "image": "/images/products/vintage-camera-strap.webp",
        "spec": "Jacquard Weave · Leather Ends · Quick Release",
        "specs": [
            "Wide Ergonomic Breathable Weave",
            "Reinforced Full-Grain Leather Ends",
            "Universal Quick-Release Mounts",
            "Adjustable 90cm to 135cm Length",
        ],
        "price": Decimal("399.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
    {
        "id": "ulanzi-carbon-tripod",
        "name": "Carbon Travel Tripod with Prompter Rig",
        "brand": "Ulanzi",
        "category_slug": "tripod",
        "description": "Ultra-lightweight multi-section carbon fiber video and photo tripod equipped with fluid panoramic ball head, phone/teleprompter display bracket, and Arca-Swiss mount.",
        "image": "/images/products/ulanzi-carbon-tripod.webp",
        "spec": "Carbon Fibre · Teleprompter Rig · Arca-Swiss Head",
        "specs": [
            "High-Strength 8-Layer Carbon Fiber",
            "Dual Panoramic Ball Head",
            "Integrated Teleprompter/Monitor Mount",
            "Max Height 160cm · Folded 38cm",
        ],
        "price": Decimal("799.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
    {
        "id": "dji-rs3-pro",
        "name": "DJI RS3 Pro Gimbal",
        "brand": "DJI",
        "category_slug": "gimbal",
        "description": "Automated 3-axis motorized camera stabilizer with extended carbon fiber axis arms, vertical shooting mount, 4.5kg tested payload, and SuperSmooth algorithm.",
        "image": "/images/products/dji-rs3-pro.webp",
        "spec": "3-Axis Motorized · Vertical Mount · 4.5kg Payload",
        "specs": [
            "Carbon Fiber Construction",
            "Automated Axis Locks",
            "Native Vertical Shooting Plate for RS3",
            "LiDAR Autofocus Compatibility",
        ],
        "price": Decimal("1899.00"),
        "availability": AvailabilityStatus.AVAILABLE,
        "is_featured": True,
        "is_rentable": True,
    },
]

# -------------------------------------------------------------------------
# Exact 3 Creator Kits with authoritative included items and unambiguous links
# -------------------------------------------------------------------------
CREATOR_KITS_SEED_DATA: List[Dict[str, Any]] = [
    {
        "kit_id": "insta360-luna-ultra",
        "title": "Insta360 Luna Ultra Creator Bundle",
        "tag": "ULTRA 360 / IMMERSIVE",
        "intended_use": "Next-generation 8K 360° capture, interactive virtual tours, high-motion vlogging, and dual-lens creative storytelling.",
        "description": "The all-in-one handheld dual-lens ultra creator bundle. Features dual Leica optics, integrated touchscreen monitor, wireless audio receiver, magnetic battery modules, and protective travel case.",
        "image": "/images/kits/insta360-luna-ultra.webp",
        "price": Decimal("3899.00"),
        "sort_order": 1,
        "items": [
            {"role": "Dual-Lens Camera", "name": "Insta360 Dual-Lens 8K Master Body", "catalogue_slug": None, "sort_order": 1},
            {"role": "Monitoring & Control", "name": "Flip Touchscreen Display & Smart Grip", "catalogue_slug": None, "sort_order": 2},
            {"role": "Audio & Wireless", "name": "Snap-On Wireless Mic Transmitter & Receiver", "catalogue_slug": None, "sort_order": 3},
            {"role": "Power & Storage", "name": "Dual Expansion Battery Packs & Protective Case", "catalogue_slug": None, "sort_order": 4},
        ],
    },
    {
        "kit_id": "content-creator-kit",
        "title": "Content Creator Kit",
        "tag": "STREAMING / WORKSPACE",
        "intended_use": "Professional YouTube studio setups, live streaming, desktop b-roll production, and high-engagement content workflows.",
        "description": "The ultimate desktop and studio workstation setup. Complete with hybrid camera body, bi-color ring light with smartphone/camera mount, shotgun audio, tabletop flex tripod, and monitoring interface.",
        "image": "/images/kits/content-creator-kit.webp",
        "price": Decimal("4999.00"),
        "sort_order": 2,
        "items": [
            {"role": "Production Camera", "name": "Sony FX30 Cinema Hybrid", "catalogue_slug": "sony-fx30", "sort_order": 1},
            {"role": "Lighting Ring", "name": "Bi-Color Studio Ring Light with Stand", "catalogue_slug": None, "sort_order": 2},
            {"role": "Support & Mount", "name": "Flexible Articulating GorillaPod & Phone Mount", "catalogue_slug": None, "sort_order": 3},
            {"role": "Audio & Power", "name": "On-Camera Shotgun Mic & USB-C Power Rig", "catalogue_slug": None, "sort_order": 4},
        ],
    },
    {
        "kit_id": "canon-content-creator",
        "title": "Canon Content Creator Kit",
        "tag": "CREATOR / HYBRID",
        "intended_use": "Vlogging, run-and-gun documentary, travel filmmaking, and Decisive Moment photo & 4K video storytelling.",
        "description": "Official Canon Creator Pack centered on the compact EOS R50 / R6 mirrorless platform. Bundled with the versatile RF-S zoom lens, Canon HG-100TBR tripod grip with wireless remote, and directional stereo microphone with deadcat windscreen.",
        "image": "/images/kits/canon-content-creator.webp",
        "price": Decimal("4299.00"),
        "sort_order": 3,
        "items": [
            {"role": "Mirrorless Camera", "name": "Canon EOS Mirrorless Body (4K Uncropped)", "catalogue_slug": None, "sort_order": 1},
            {"role": "Standard Zoom Lens", "name": "Canon RF-S 18–45mm f/4.5–6.3 IS STM", "catalogue_slug": None, "sort_order": 2},
            {"role": "Tripod Grip", "name": "Canon HG-100TBR Wireless Remote Tripod Grip", "catalogue_slug": None, "sort_order": 3},
            {"role": "Directional Audio", "name": "Canon DM-E100 Stereo Microphone with Deadcat", "catalogue_slug": None, "sort_order": 4},
        ],
    },
]


def seed_database(db: Session) -> Dict[str, int]:
    """
    Idempotent seeding function:
    - Inserts or updates 8 categories
    - Inserts or updates 12 equipment records
    - Inserts or updates 3 creator kits and their bundled components
    - Does not delete unrelated records
    """
    counts = {"categories": 0, "equipment": 0, "kits": 0, "kit_items": 0}

    # 1. Seed Categories
    category_map: Dict[str, Category] = {}
    for cat_data in CATEGORIES_SEED_DATA:
        cat = db.scalar(select(Category).where(Category.slug == cat_data["slug"]))
        if not cat:
            cat = Category(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                sort_order=cat_data["sort_order"],
                is_visible_in_category_section=cat_data["is_visible_in_category_section"],
                is_active=True,
            )
            db.add(cat)
            db.flush()
        else:
            cat.name = cat_data["name"]
            cat.description = cat_data["description"]
            cat.sort_order = cat_data["sort_order"]
            cat.is_visible_in_category_section = cat_data["is_visible_in_category_section"]
            cat.is_active = True
        category_map[cat.slug] = cat
        counts["categories"] += 1

    # 2. Seed Equipment
    equipment_map: Dict[str, Equipment] = {}
    for eq_data in EQUIPMENT_SEED_DATA:
        cat = category_map[eq_data["category_slug"]]
        item = db.scalar(select(Equipment).where(Equipment.product_id == eq_data["id"]))
        if not item:
            item = Equipment(
                product_id=eq_data["id"],
                name=eq_data["name"],
                brand=eq_data["brand"],
                category_id=cat.id,
                description=eq_data["description"],
                image=eq_data["image"],
                spec=eq_data["spec"],
                specs=eq_data["specs"],
                price=eq_data["price"],
                availability=eq_data["availability"],
                is_featured=eq_data["is_featured"],
                is_rentable=eq_data["is_rentable"],
                is_active=True,
            )
            db.add(item)
            db.flush()
        else:
            item.name = eq_data["name"]
            item.brand = eq_data["brand"]
            item.category_id = cat.id
            item.description = eq_data["description"]
            item.image = eq_data["image"]
            item.spec = eq_data["spec"]
            item.specs = eq_data["specs"]
            item.price = eq_data["price"]
            item.availability = eq_data["availability"]
            item.is_featured = eq_data["is_featured"]
            item.is_rentable = eq_data["is_rentable"]
            item.is_active = True
        equipment_map[item.product_id] = item
        counts["equipment"] += 1

    # 3. Seed Creator Kits & Items
    for kit_data in CREATOR_KITS_SEED_DATA:
        kit = db.scalar(select(CreatorKit).where(CreatorKit.kit_id == kit_data["kit_id"]))
        if not kit:
            kit = CreatorKit(
                kit_id=kit_data["kit_id"],
                title=kit_data["title"],
                tag=kit_data["tag"],
                intended_use=kit_data["intended_use"],
                description=kit_data["description"],
                image=kit_data["image"],
                price=kit_data["price"],
                sort_order=kit_data["sort_order"],
                is_active=True,
            )
            db.add(kit)
            db.flush()
        else:
            kit.title = kit_data["title"]
            kit.tag = kit_data["tag"]
            kit.intended_use = kit_data["intended_use"]
            kit.description = kit_data["description"]
            kit.image = kit_data["image"]
            kit.price = kit_data["price"]
            kit.sort_order = kit_data["sort_order"]
            kit.is_active = True

        counts["kits"] += 1

        # Seed kit items safely: remove prior items and insert fresh to maintain order and unambiguous links
        db.query(CreatorKitItem).filter(CreatorKitItem.kit_id == kit.id).delete()
        db.flush()

        for item_data in kit_data["items"]:
            eq_link = equipment_map.get(item_data["catalogue_slug"]) if item_data["catalogue_slug"] else None
            kit_item = CreatorKitItem(
                kit_id=kit.id,
                role=item_data["role"],
                name=item_data["name"],
                equipment_id=eq_link.id if eq_link else None,
                quantity=1,
                sort_order=item_data["sort_order"],
            )
            db.add(kit_item)
            counts["kit_items"] += 1

    db.commit()
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting database seeding...")
    with SessionLocal() as session:
        result = seed_database(session)
        logger.info("Database seeding completed successfully: %s", result)
