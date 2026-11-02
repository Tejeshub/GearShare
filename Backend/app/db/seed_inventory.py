import logging
from datetime import date
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.catalog import Equipment
from app.models.inventory import EquipmentUnit, UnitCondition, UnitOperationalStatus

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Development Inventory Configuration
# Modify these quantities below to adjust sample unit stock per product category:
# -----------------------------------------------------------------------------
CATEGORY_QUANTITY_MAPPING: Dict[str, int] = {
    "cameras": 3,        # Cameras: 3 per product (4 products * 3 = 12 units)
    "lenses": 2,         # Lenses: 2 per product (2 products * 2 = 4 units)
    "lighting": 2,       # Lighting: 2 per product (1 product * 2 = 2 units)
    "stabilization": 2,  # Stabilization: 2 per product (1 product * 2 = 2 units)
    "car-mount": 2,      # Car Mount: 2 units
    "camera-strap": 4,   # Camera Strap: 4 units
    "tripod": 3,         # Tripod: 3 units
    "gimbal": 2,         # Gimbal: 2 units
}

# Total expected units across all 12 products:
# 12 (cameras) + 4 (lenses) + 2 (lighting) + 2 (stabilization) + 2 (car-mount) + 4 (strap) + 3 (tripod) + 2 (gimbal) = 31 units

# Short prefix for asset codes
CATEGORY_PREFIX_MAPPING: Dict[str, str] = {
    "cameras": "CAM",
    "lenses": "LNS",
    "lighting": "LGT",
    "stabilization": "STB",
    "car-mount": "MNT",
    "camera-strap": "STP",
    "tripod": "TRP",
    "gimbal": "GMB",
}


def seed_inventory(db: Session) -> Dict[str, int]:
    """
    Idempotent seeding of physical equipment units for existing catalogue products.
    - Stable asset code generation (e.g. GS-CAM-001, GS-CAM-002, etc.)
    - Does NOT duplicate existing units
    - Does NOT overwrite condition, operational status, or custom notes on existing units
    - Does NOT delete existing units
    """
    stmt = select(Equipment).order_by(Equipment.product_id.asc())
    equipment_list = db.scalars(stmt).all()

    created_count = 0
    existing_count = 0

    # Running counters per category prefix to guarantee sequential, deterministic asset codes
    category_counters: Dict[str, int] = {}

    for eq in equipment_list:
        cat_slug = eq.category.slug if eq.category else "gen"
        prefix = CATEGORY_PREFIX_MAPPING.get(cat_slug, "GEN")
        target_qty = CATEGORY_QUANTITY_MAPPING.get(cat_slug, 2)

        for unit_idx in range(1, target_qty + 1):
            category_counters[prefix] = category_counters.get(prefix, 0) + 1
            seq_num = category_counters[prefix]
            asset_code = f"GS-{prefix}-{seq_num:03d}"
            serial_num = f"SN-{prefix}-{seq_num:04d}"

            # Check if asset_code already exists
            existing_unit = db.scalar(
                select(EquipmentUnit).where(EquipmentUnit.asset_code == asset_code)
            )

            if not existing_unit:
                unit = EquipmentUnit(
                    equipment_id=eq.id,
                    asset_code=asset_code,
                    serial_number=serial_num,
                    condition=UnitCondition.EXCELLENT,
                    operational_status=UnitOperationalStatus.ACTIVE,
                    purchase_date=date(2026, 1, 15),
                    notes=f"Initial stock for {eq.name}",
                )
                db.add(unit)
                created_count += 1
            else:
                existing_count += 1

    db.commit()
    logger.info(
        "Inventory seeding finished: %d created, %d already present",
        created_count,
        existing_count,
    )
    return {"created": created_count, "existing": existing_count, "total": created_count + existing_count}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Seeding physical inventory...")
    with SessionLocal() as session:
        res = seed_inventory(session)
        logger.info("Result: %s", res)
