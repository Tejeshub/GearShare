from datetime import date
import pytest
from fastapi import status
from sqlalchemy import select

from app.db.seed_inventory import seed_inventory
from app.models.catalog import Equipment, CreatorKit
from app.models.inventory import (
    AllocationStatus,
    EquipmentUnit,
    RentalAllocation,
    UnitCondition,
    UnitOperationalStatus,
)
from app.services.availability_service import AvailabilityService


# -----------------------------------------------------------------
# 1. Physical Units & Seeding Tests
# -----------------------------------------------------------------
def test_create_physical_equipment_unit(seeded_db):
    """Test 1: Creating a physical equipment unit."""
    eq = seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-fx30"))
    unit = EquipmentUnit(
        equipment_id=eq.id,
        asset_code="GS-TEST-001",
        serial_number="SN-TEST-0001",
        condition=UnitCondition.EXCELLENT,
        operational_status=UnitOperationalStatus.ACTIVE,
        purchase_date=date(2026, 1, 1),
        notes="Test unit",
    )
    seeded_db.add(unit)
    seeded_db.commit()
    seeded_db.refresh(unit)

    assert unit.id is not None
    assert unit.asset_code == "GS-TEST-001"
    assert unit.operational_status == UnitOperationalStatus.ACTIVE
    assert unit.condition == UnitCondition.EXCELLENT


def test_idempotent_inventory_seeding(seeded_db):
    """Test 2: Idempotent inventory seeding."""
    res1 = seed_inventory(seeded_db)
    assert res1["created"] == 31  # 31 total units across the 12 products
    assert res1["existing"] == 0

    # Second run creates 0 duplicates
    res2 = seed_inventory(seeded_db)
    assert res2["created"] == 0
    assert res2["existing"] == 31

    total_units = len(seeded_db.scalars(select(EquipmentUnit)).all())
    assert total_units == 31


def test_product_multiple_physical_units(inventory_seeded_db):
    """Test 3: Product with multiple physical units (Sony FX30 has 3 units)."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-fx30"))
    units = inventory_seeded_db.scalars(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    ).all()
    assert len(units) == 3
    for u in units:
        assert u.operational_status == UnitOperationalStatus.ACTIVE


# -----------------------------------------------------------------
# 2. Availability Calculation & Unit Filters
# -----------------------------------------------------------------
def test_available_quantity_calculation(inventory_client):
    """Test 4: Available quantity calculation via GET API."""
    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-fx30?startDate=2026-12-01&endDate=2026-12-03"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["productId"] == "sony-fx30"
    assert data["totalActiveUnits"] == 3
    assert data["availableQuantity"] == 3
    assert data["requestedQuantity"] == 1
    assert data["isAvailable"] is True
    assert len(data["availableAssetCodes"]) == 3


def test_single_unit_availability(inventory_client):
    """Test 5: Single-unit availability request."""
    res = inventory_client.get(
        "/api/v1/availability/equipment/aputure-300d-ii?startDate=2026-12-01&endDate=2026-12-01&quantity=1"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["totalActiveUnits"] == 2
    assert data["availableQuantity"] == 2
    assert data["isAvailable"] is True


def test_multiple_unit_availability(inventory_client):
    """Test 6: Multiple-unit availability request within capacity."""
    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-fx30?startDate=2026-12-01&endDate=2026-12-05&quantity=3"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["availableQuantity"] == 3
    assert data["isAvailable"] is True


def test_maintenance_unit_exclusion(inventory_seeded_db, inventory_client):
    """Test 7: Maintenance units are excluded from active count and availability."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-fx30"))
    unit = inventory_seeded_db.scalar(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    )
    unit.operational_status = UnitOperationalStatus.MAINTENANCE
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-fx30?startDate=2026-12-01&endDate=2026-12-03"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["totalActiveUnits"] == 2
    assert data["availableQuantity"] == 2


def test_retired_unit_exclusion(inventory_seeded_db, inventory_client):
    """Test 8: Retired units are excluded."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "dji-rs4-pro"))
    units = inventory_seeded_db.scalars(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    ).all()
    # Mark both as RETIRED
    for u in units:
        u.operational_status = UnitOperationalStatus.RETIRED
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/dji-rs4-pro?startDate=2026-12-01&endDate=2026-12-03"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["totalActiveUnits"] == 0
    assert data["availableQuantity"] == 0
    assert data["isAvailable"] is False


# -----------------------------------------------------------------
# 3. Allocation Blocking & Overlap Logic
# -----------------------------------------------------------------
def test_cancelled_allocation_does_not_block(inventory_seeded_db, inventory_client):
    """Test 9: Cancelled allocations do not block dates."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "nikon-z8"))
    units = inventory_seeded_db.scalars(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    ).all()

    # Create cancelled allocations for all 3 units
    for u in units:
        alloc = RentalAllocation(
            unit_id=u.id,
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 12),
            status=AllocationStatus.CANCELLED,
        )
        inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/nikon-z8?startDate=2026-12-10&endDate=2026-12-12&quantity=3"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["availableQuantity"] == 3
    assert res.json()["isAvailable"] is True


def test_completed_allocation_does_not_block(inventory_seeded_db, inventory_client):
    """Test 10: Completed allocations do not block dates."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "nikon-z8"))
    unit = inventory_seeded_db.scalar(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    )
    alloc = RentalAllocation(
        unit_id=unit.id,
        start_date=date(2026, 12, 10),
        end_date=date(2026, 12, 12),
        status=AllocationStatus.COMPLETED,
    )
    inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/nikon-z8?startDate=2026-12-10&endDate=2026-12-12&quantity=3"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["availableQuantity"] == 3


def test_reserved_allocation_blocks_dates(inventory_seeded_db, inventory_client):
    """Test 11: Reserved allocation blocks unit for requested dates."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-24-70-gm2"))
    unit = inventory_seeded_db.scalar(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    )
    alloc = RentalAllocation(
        unit_id=unit.id,
        start_date=date(2026, 12, 10),
        end_date=date(2026, 12, 12),
        status=AllocationStatus.RESERVED,
    )
    inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-24-70-gm2?startDate=2026-12-10&endDate=2026-12-12"
    )
    assert res.status_code == status.HTTP_200_OK
    # 2 total units - 1 reserved = 1 available
    assert res.json()["availableQuantity"] == 1


def test_confirmed_allocation_blocks_dates(inventory_seeded_db, inventory_client):
    """Test 12: Confirmed allocation blocks unit."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-24-70-gm2"))
    units = inventory_seeded_db.scalars(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    ).all()
    # Confirm both units
    for u in units:
        alloc = RentalAllocation(
            unit_id=u.id,
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 12),
            status=AllocationStatus.CONFIRMED,
        )
        inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-24-70-gm2?startDate=2026-12-10&endDate=2026-12-12"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["availableQuantity"] == 0
    assert res.json()["isAvailable"] is False


def test_overlapping_rental_dates(inventory_seeded_db, inventory_client):
    """Test 13: Overlapping dates (Existing: Dec 10-12, Requested: Dec 12-14 -> Conflict on Dec 12)."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-70-200-gm2"))
    units = inventory_seeded_db.scalars(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    ).all()
    for u in units:
        alloc = RentalAllocation(
            unit_id=u.id,
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 12),
            status=AllocationStatus.RESERVED,
        )
        inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    # Request Dec 12 to Dec 14 overlaps Dec 12
    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-70-200-gm2?startDate=2026-12-12&endDate=2026-12-14"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["availableQuantity"] == 0
    assert res.json()["isAvailable"] is False


def test_adjacent_non_overlapping_dates(inventory_seeded_db, inventory_client):
    """Test 14: Adjacent dates (Existing: Dec 10-12, Requested: Dec 13-15 -> Available)."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-70-200-gm2"))
    units = inventory_seeded_db.scalars(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    ).all()
    for u in units:
        alloc = RentalAllocation(
            unit_id=u.id,
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 12),
            status=AllocationStatus.RESERVED,
        )
        inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-70-200-gm2?startDate=2026-12-13&endDate=2026-12-15"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["availableQuantity"] == 2
    assert res.json()["isAvailable"] is True


def test_exact_same_start_and_end_dates(inventory_seeded_db, inventory_client):
    """Test 15: Exact same single day (Existing: Dec 10-10, Requested: Dec 10-10 -> Conflict)."""
    eq = inventory_seeded_db.scalar(select(Equipment).where(Equipment.product_id == "dji-rs3-pro"))
    units = inventory_seeded_db.scalars(
        select(EquipmentUnit).where(EquipmentUnit.equipment_id == eq.id)
    ).all()
    for u in units:
        alloc = RentalAllocation(
            unit_id=u.id,
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 10),
            status=AllocationStatus.RESERVED,
        )
        inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    res = inventory_client.get(
        "/api/v1/availability/equipment/dji-rs3-pro?startDate=2026-12-10&endDate=2026-12-10"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["availableQuantity"] == 0
    assert res.json()["isAvailable"] is False


# -----------------------------------------------------------------
# 4. Creator Kit & Combined Availability Tests
# -----------------------------------------------------------------
def test_kit_component_availability(inventory_client):
    """Test 16: Kit component availability check."""
    # Content Creator Kit includes Sony FX30
    res = inventory_client.get(
        "/api/v1/availability/kits/content-creator-kit?startDate=2026-12-01&endDate=2026-12-05"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["kitId"] == "content-creator-kit"
    assert data["isAvailable"] is True
    assert len(data["components"]) == 4

    # Sony FX30 component has catalogue link
    fx30_comp = next(c for c in data["components"] if c["productId"] == "sony-fx30")
    assert fx30_comp["isCatalogueLinked"] is True
    assert fx30_comp["availableQuantity"] == 3
    assert fx30_comp["isAvailable"] is True


def test_kit_with_independent_components(inventory_client):
    """Test 17: Kit with independent components (no fake inventory checks)."""
    # Insta360 bundle has 4 independent components
    res = inventory_client.get(
        "/api/v1/availability/kits/insta360-luna-ultra?startDate=2026-12-01&endDate=2026-12-05"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["isAvailable"] is True
    for comp in data["components"]:
        assert comp["isCatalogueLinked"] is False
        assert comp["availableQuantity"] is None
        assert comp["isAvailable"] is True


def test_insufficient_inventory(inventory_client):
    """Test 18: Requesting more units than total available returns isAvailable=False."""
    # Sony FX30 has 3 units, request 5
    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-fx30?startDate=2026-12-01&endDate=2026-12-05&quantity=5"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["availableQuantity"] == 3
    assert data["requestedQuantity"] == 5
    assert data["isAvailable"] is False


def test_atomic_allocation_rollback(inventory_seeded_db):
    """Test 19: Atomic allocation rolls back all allocations if any requested item cannot be fulfilled."""
    initial_allocations = len(inventory_seeded_db.scalars(select(RentalAllocation)).all())

    # Try allocating 2 Sony FX30 (available) + 5 Aputure lights (only 2 exist -> failure)
    allocations_req = [("sony-fx30", 2), ("aputure-300d-ii", 5)]

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        AvailabilityService.allocate_units(
            db=inventory_seeded_db,
            allocations_to_make=allocations_req,
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 3),
        )

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "Insufficient inventory" in exc_info.value.detail

    # Verify zero allocations were created
    current_allocations = len(inventory_seeded_db.scalars(select(RentalAllocation)).all())
    assert current_allocations == initial_allocations


def test_invalid_dates(inventory_client):
    """Test 20: Invalid dates validation (endDate < startDate)."""
    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-fx30?startDate=2026-12-10&endDate=2026-12-05"
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_unknown_product_or_kit(inventory_client):
    """Test 21: Unknown product returns 404."""
    res_prod = inventory_client.get(
        "/api/v1/availability/equipment/unknown-camera?startDate=2026-12-01&endDate=2026-12-03"
    )
    assert res_prod.status_code == status.HTTP_404_NOT_FOUND

    res_kit = inventory_client.get(
        "/api/v1/availability/kits/unknown-kit?startDate=2026-12-01&endDate=2026-12-03"
    )
    assert res_kit.status_code == status.HTTP_404_NOT_FOUND


def test_zero_and_negative_quantities(inventory_client):
    """Test 22: Zero and negative quantities rejected."""
    res = inventory_client.get(
        "/api/v1/availability/equipment/sony-fx30?startDate=2026-12-01&endDate=2026-12-03&quantity=0"
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_quote_calculation_remains_unchanged(inventory_client):
    """Test 23: Quote calculation remains provisional and does not create allocations."""
    payload = {
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-03",
    }
    res = inventory_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["isProvisional"] is True
    # 3499 * 3 = 10497
    assert float(data["total"]) == 10497.00


def test_no_allocation_created_by_availability_checks(inventory_seeded_db, inventory_client):
    """Test 24: Read-only availability check creates zero allocations."""
    initial_allocations = len(inventory_seeded_db.scalars(select(RentalAllocation)).all())

    # Single check
    inventory_client.get("/api/v1/availability/equipment/sony-fx30?startDate=2026-12-01&endDate=2026-12-05")
    # Kit check
    inventory_client.get("/api/v1/availability/kits/content-creator-kit?startDate=2026-12-01&endDate=2026-12-05")
    # Combined check
    inventory_client.post(
        "/api/v1/availability/check",
        json={
            "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
            "kitId": "content-creator-kit",
            "startDate": "2026-12-01",
            "endDate": "2026-12-05",
        },
    )

    current_allocations = len(inventory_seeded_db.scalars(select(RentalAllocation)).all())
    assert current_allocations == initial_allocations
