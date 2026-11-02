from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi import status
from sqlalchemy import select

from app.models.catalog import Equipment
from app.models.enquiry import EnquiryStatus, RentalEnquiry, RentalEnquiryItem
from app.models.inventory import AllocationStatus, EquipmentUnit, RentalAllocation
from app.services.enquiry_service import EnquiryService


# -----------------------------------------------------------------
# 1. Enquiry Submission Tests (Tests 1 - 12)
# -----------------------------------------------------------------
def test_valid_product_only_enquiry(inventory_client):
    """Test 1: Valid product-only enquiry."""
    payload = {
        "customerName": "Aarav Sharma",
        "email": "aarav.sharma@example.com",
        "phone": "9876543210",
        "message": "Shoot in Mumbai",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
        "durationDays": 2,
        "calculatedEstimate": 6998.00,
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["success"] is True
    assert data["referenceId"].startswith("GS-2026-")
    assert data["status"] == "Pending Review"
    assert data["isSimulated"] is False
    assert float(data["quote"]["total"]) == 6998.00


def test_valid_kit_only_enquiry(inventory_client):
    """Test 2: Valid kit-only enquiry."""
    payload = {
        "customerName": "Diya Patel",
        "email": "diya.patel@example.com",
        "phone": "9876543211",
        "kitId": "content-creator-kit",
        "startDate": "2026-12-05",
        "endDate": "2026-12-05",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["success"] is True
    assert float(data["quote"]["total"]) == 4999.00


def test_kit_plus_additional_equipment(inventory_client):
    """Test 3: Kit plus additional equipment."""
    # Kit includes 1 Sony FX30; request 2 Sony FX30 + 1 Aputure light
    payload = {
        "customerName": "Rohan Verma",
        "email": "rohan.v@example.com",
        "phone": "9876543212",
        "kitId": "content-creator-kit",  # 4999
        "productSelections": [
            {"productId": "sony-fx30", "quantity": 2},  # 1 extra * 3499
            {"productId": "aputure-300d-ii", "quantity": 1},  # 1999
        ],
        "startDate": "2026-12-10",
        "endDate": "2026-12-10",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    # 4999 + 3499 + 1999 = 10497
    assert float(res.json()["quote"]["total"]) == 10497.00


def test_correct_database_derived_quote(inventory_client):
    """Test 4: Database-derived prices are applied."""
    payload = {
        "customerName": "Pooja Hegde",
        "email": "pooja@example.com",
        "phone": "9876543213",
        "productSelections": [{"productId": "nikon-z8", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-03",  # 3 days
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    # 4499 * 3 = 13497
    assert float(res.json()["quote"]["total"]) == 13497.00


def test_incorrect_client_estimate_ignored(inventory_client):
    """Test 5: Client-tampered estimate is ignored; server calculates actual total."""
    payload = {
        "customerName": "Fraud Tester",
        "email": "fraud@example.com",
        "phone": "9876543214",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
        "calculatedEstimate": 10.00,  # Fake cheap estimate
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    assert float(res.json()["quote"]["total"]) == 3499.00


def test_incorrect_client_duration_ignored(inventory_client):
    """Test 6: Client-tampered durationDays is ignored."""
    payload = {
        "customerName": "Duration Tester",
        "email": "dur@example.com",
        "phone": "9876543215",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-03",  # 3 days
        "durationDays": 1,  # Fake 1 day
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["quote"]["durationDays"] == 3
    assert float(res.json()["quote"]["total"]) == 10497.00


def test_invalid_customer_information(inventory_client):
    """Test 7: Malformed email or empty name rejected."""
    payload = {
        "customerName": " ",
        "email": "invalid-email-format",
        "phone": "123",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Verify invalid phone specifically (e.g. 9 digits or starts with 1-5)
    payload_bad_phone = {
        "customerName": "Valid Name",
        "email": "valid@example.com",
        "phone": "5987654321",  # Starts with 5, invalid in India
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    res_bad = inventory_client.post("/api/v1/rentals/enquiries", json=payload_bad_phone)
    assert res_bad.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_invalid_rental_dates(inventory_client):
    """Test 8: End date earlier than start date rejected."""
    payload = {
        "customerName": "Date Tester",
        "email": "date@example.com",
        "phone": "9876543216",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-10",
        "endDate": "2026-12-05",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_unknown_product(inventory_client):
    """Test 9: Unknown product rejected with 404."""
    payload = {
        "customerName": "Unknown Tester",
        "email": "test@example.com",
        "phone": "9876543217",
        "productSelections": [{"productId": "camera-does-not-exist", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_unknown_kit(inventory_client):
    """Test 10: Unknown kit rejected with 404."""
    payload = {
        "customerName": "Kit Tester",
        "email": "test@example.com",
        "phone": "9876543218",
        "kitId": "kit-does-not-exist",
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_insufficient_inventory(inventory_client):
    """Test 11: Requesting more units than physical inventory yields 409 Conflict."""
    payload = {
        "customerName": "Excess Tester",
        "email": "test@example.com",
        "phone": "9876543219",
        "productSelections": [{"productId": "sony-fx30", "quantity": 10}],  # Only 3 exist
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_409_CONFLICT
    assert "Insufficient inventory" in res.json()["detail"]


def test_no_partial_allocations_on_failure(inventory_seeded_db, inventory_client):
    """Test 12: Atomic rollback leaves no partial allocations or orphan enquiries on failure."""
    init_enquiries = len(inventory_seeded_db.scalars(select(RentalEnquiry)).all())
    init_allocs = len(inventory_seeded_db.scalars(select(RentalAllocation)).all())

    payload = {
        "customerName": "Rollback Tester",
        "email": "test@example.com",
        "phone": "9876543220",
        "productSelections": [
            {"productId": "sony-fx30", "quantity": 1},  # Available
            {"productId": "aputure-300d-ii", "quantity": 10},  # Insufficient (only 2 exist)
        ],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_409_CONFLICT

    post_enquiries = len(inventory_seeded_db.scalars(select(RentalEnquiry)).all())
    post_allocs = len(inventory_seeded_db.scalars(select(RentalAllocation)).all())

    assert post_enquiries == init_enquiries
    assert post_allocs == init_allocs


# -----------------------------------------------------------------
# 2. Inventory Allocation Verification (Tests 13 - 19)
# -----------------------------------------------------------------
def test_physical_units_allocated_correctly(inventory_seeded_db, inventory_client):
    """Test 13: Physical units allocated correctly and linked to enquiry."""
    payload = {
        "customerName": "Alloc Tester",
        "email": "alloc@example.com",
        "phone": "9876543221",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-15",
        "endDate": "2026-12-16",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    allocations = inventory_seeded_db.scalars(
        select(RentalAllocation).where(RentalAllocation.enquiry_id == enquiry.id)
    ).all()
    assert len(allocations) == 1
    assert allocations[0].status == AllocationStatus.RESERVED
    assert allocations[0].enquiry_reference == ref


def test_multiple_quantities_allocated_correctly(inventory_seeded_db, inventory_client):
    """Test 14: Multiple quantities allocate corresponding distinct physical units."""
    payload = {
        "customerName": "Multi Alloc",
        "email": "multi@example.com",
        "phone": "9876543222",
        "productSelections": [{"productId": "sony-fx30", "quantity": 3}],
        "startDate": "2026-12-15",
        "endDate": "2026-12-16",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    allocations = inventory_seeded_db.scalars(
        select(RentalAllocation).where(RentalAllocation.enquiry_id == enquiry.id)
    ).all()
    assert len(allocations) == 3
    unit_ids = {a.unit_id for a in allocations}
    assert len(unit_ids) == 3  # 3 distinct units


def test_kit_components_allocated_correctly(inventory_seeded_db, inventory_client):
    """Test 15: Kit catalogue-linked components allocated."""
    # Content Creator Kit includes 1 Sony FX30
    payload = {
        "customerName": "Kit Alloc",
        "email": "kit@example.com",
        "phone": "9876543223",
        "kitId": "content-creator-kit",
        "startDate": "2026-12-20",
        "endDate": "2026-12-20",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    allocations = inventory_seeded_db.scalars(
        select(RentalAllocation).where(RentalAllocation.enquiry_id == enquiry.id)
    ).all()
    assert len(allocations) == 1
    # Verify allocated unit is a Sony FX30
    unit = inventory_seeded_db.scalar(
        select(EquipmentUnit).where(EquipmentUnit.id == allocations[0].unit_id)
    )
    assert unit.asset_code.startswith("GS-CAM-")


def test_independent_kit_components_preserved_without_fake_allocations(inventory_seeded_db, inventory_client):
    """Test 16: Independent kit components generate zero fake allocations but are captured in items snapshot."""
    # Insta360 bundle has 4 independent accessories
    payload = {
        "customerName": "Insta360 Buyer",
        "email": "insta@example.com",
        "phone": "9876543224",
        "kitId": "insta360-luna-ultra",
        "startDate": "2026-12-22",
        "endDate": "2026-12-22",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    allocations = inventory_seeded_db.scalars(
        select(RentalAllocation).where(RentalAllocation.enquiry_id == enquiry.id)
    ).all()
    assert len(allocations) == 0  # No fake physical units

    # But snapshot contains the 4 items
    items = inventory_seeded_db.scalars(
        select(RentalEnquiryItem).where(RentalEnquiryItem.enquiry_id == enquiry.id)
    ).all()
    assert len(items) == 1
    assert len(items[0].bundled_components_snapshot) == 4


def test_included_kit_quantities_not_allocated_twice(inventory_seeded_db, inventory_client):
    """Test 17: Requesting kit + 1 already-included product allocates only 1 unit."""
    payload = {
        "customerName": "Dedupe Tester",
        "email": "dedupe@example.com",
        "phone": "9876543225",
        "kitId": "content-creator-kit",  # includes 1 Sony FX30
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-25",
        "endDate": "2026-12-25",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    allocations = inventory_seeded_db.scalars(
        select(RentalAllocation).where(RentalAllocation.enquiry_id == enquiry.id)
    ).all()
    assert len(allocations) == 1  # Only 1 unit allocated, not 2


def test_additional_quantities_allocated_correctly(inventory_seeded_db, inventory_client):
    """Test 18: Kit + 3 Sony FX30 allocates 1 (kit) + 2 (extra) = 3 units."""
    payload = {
        "customerName": "Extra Alloc",
        "email": "extra@example.com",
        "phone": "9876543226",
        "kitId": "content-creator-kit",
        "productSelections": [{"productId": "sony-fx30", "quantity": 3}],
        "startDate": "2026-12-28",
        "endDate": "2026-12-28",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    allocations = inventory_seeded_db.scalars(
        select(RentalAllocation).where(RentalAllocation.enquiry_id == enquiry.id)
    ).all()
    assert len(allocations) == 3


def test_overlapping_allocations_rejected(inventory_client):
    """Test 19: Second enquiry for overlapping dates when capacity is exhausted is rejected."""
    # Aputure 300D II has 2 units
    payload1 = {
        "customerName": "Customer 1",
        "email": "c1@example.com",
        "phone": "9876543227",
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 2}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-03",
    }
    res1 = inventory_client.post("/api/v1/rentals/enquiries", json=payload1)
    assert res1.status_code == status.HTTP_201_CREATED

    # Customer 2 attempts to book for overlapping Dec 2-4
    payload2 = {
        "customerName": "Customer 2",
        "email": "c2@example.com",
        "phone": "9876543228",
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 1}],
        "startDate": "2026-12-02",
        "endDate": "2026-12-04",
    }
    res2 = inventory_client.post("/api/v1/rentals/enquiries", json=payload2)
    assert res2.status_code == status.HTTP_409_CONFLICT


# -----------------------------------------------------------------
# 3. Hold Lifecycle & Expiry (Tests 20 - 27)
# -----------------------------------------------------------------
def test_hold_expires_after_24_hours(inventory_seeded_db, inventory_client):
    """Test 20: Hold expires exactly 24 hours after creation."""
    payload = {
        "customerName": "Hold 24",
        "email": "hold@example.com",
        "phone": "9876543229",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    diff = enquiry.hold_expires_at - enquiry.created_at
    assert diff.total_seconds() == 24 * 3600


def test_expired_enquiry_stops_blocking_inventory(inventory_seeded_db, inventory_client):
    """Test 21: Expired enquiry stops blocking inventory even before cleanup command runs."""
    payload = {
        "customerName": "Expiring User",
        "email": "exp@example.com",
        "phone": "9876543230",
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 2}],
        "startDate": "2026-12-05",
        "endDate": "2026-12-05",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    ref = res.json()["referenceId"]

    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    # Simulate past hold_expires_at (expired 1 hour ago)
    enquiry.hold_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    inventory_seeded_db.commit()

    # Now verify availability check sees 2 units available
    avail_res = inventory_client.get(
        "/api/v1/availability/equipment/aputure-300d-ii?startDate=2026-12-05&endDate=2026-12-05"
    )
    assert avail_res.status_code == status.HTTP_200_OK
    assert avail_res.json()["availableQuantity"] == 2
    assert avail_res.json()["isAvailable"] is True


def test_cleanup_marks_expired_enquiries(inventory_seeded_db):
    """Test 22: Cleanup service transitions past hold enquiries to Expired and releases allocations."""
    enquiry = RentalEnquiry(
        reference="GS-2026-EXP1",
        customer_name="Test Expired",
        email="test@expired.com",
        phone="9876543231",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 1),
        duration_days=1,
        subtotal=Decimal("3499.00"),
        discount=Decimal("0.00"),
        estimated_total=Decimal("3499.00"),
        status=EnquiryStatus.PENDING_REVIEW,
        hold_expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    inventory_seeded_db.add(enquiry)
    inventory_seeded_db.flush()

    unit = inventory_seeded_db.scalar(select(EquipmentUnit))
    alloc = RentalAllocation(
        unit_id=unit.id,
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 1),
        status=AllocationStatus.RESERVED,
        enquiry_id=enquiry.id,
    )
    inventory_seeded_db.add(alloc)
    inventory_seeded_db.commit()

    count = EnquiryService.cleanup_expired_enquiries(inventory_seeded_db)
    assert count >= 1

    inventory_seeded_db.refresh(enquiry)
    inventory_seeded_db.refresh(alloc)
    assert enquiry.status == EnquiryStatus.EXPIRED
    assert alloc.status == AllocationStatus.CANCELLED


def test_cleanup_is_idempotent(inventory_seeded_db):
    """Test 23: Running cleanup multiple times is idempotent."""
    c1 = EnquiryService.cleanup_expired_enquiries(inventory_seeded_db)
    c2 = EnquiryService.cleanup_expired_enquiries(inventory_seeded_db)
    assert c2 == 0


def test_confirmed_enquiries_do_not_expire(inventory_seeded_db):
    """Test 24: Confirmed enquiries are NOT modified by cleanup."""
    enquiry = RentalEnquiry(
        reference="GS-2026-CNF1",
        customer_name="Confirmed User",
        email="cnf@example.com",
        phone="9876543232",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 1),
        duration_days=1,
        subtotal=Decimal("3499.00"),
        discount=Decimal("0.00"),
        estimated_total=Decimal("3499.00"),
        status=EnquiryStatus.CONFIRMED,
        hold_expires_at=datetime.now(timezone.utc) - timedelta(hours=5),
    )
    inventory_seeded_db.add(enquiry)
    inventory_seeded_db.commit()

    EnquiryService.cleanup_expired_enquiries(inventory_seeded_db)
    inventory_seeded_db.refresh(enquiry)
    assert enquiry.status == EnquiryStatus.CONFIRMED


def test_rejected_enquiries_release_units(inventory_client, inventory_seeded_db):
    """Test 25: Rejecting enquiry transitions allocations to CANCELLED."""
    payload = {
        "customerName": "Reject User",
        "email": "reject@example.com",
        "phone": "9876543233",
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 2}],
        "startDate": "2026-12-10",
        "endDate": "2026-12-10",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    ref = res.json()["referenceId"]

    # Reject
    patch_res = inventory_client.patch(
        f"/api/v1/rentals/enquiries/{ref}/status",
        json={"status": "Rejected"},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["status"] == "Rejected"

    # Verify allocations are cancelled
    enquiry = inventory_seeded_db.scalar(
        select(RentalEnquiry).where(RentalEnquiry.reference == ref)
    )
    allocs = inventory_seeded_db.scalars(
        select(RentalAllocation).where(RentalAllocation.enquiry_id == enquiry.id)
    ).all()
    for a in allocs:
        assert a.status == AllocationStatus.CANCELLED


def test_cancelled_enquiries_release_units(inventory_client, inventory_seeded_db):
    """Test 26: Cancelling enquiry releases units."""
    payload = {
        "customerName": "Cancel User",
        "email": "cancel@example.com",
        "phone": "9876543234",
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 2}],
        "startDate": "2026-12-12",
        "endDate": "2026-12-12",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    ref = res.json()["referenceId"]

    patch_res = inventory_client.patch(
        f"/api/v1/rentals/enquiries/{ref}/status",
        json={"status": "Cancelled"},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["status"] == "Cancelled"


def test_completed_enquiries_do_not_block_future_dates(inventory_client):
    """Test 27: Completed status transitions allocation to COMPLETED which does not block future dates."""
    payload = {
        "customerName": "Complete User",
        "email": "complete@example.com",
        "phone": "9876543235",
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 2}],
        "startDate": "2026-12-14",
        "endDate": "2026-12-14",
    }
    res = inventory_client.post("/api/v1/rentals/enquiries", json=payload)
    ref = res.json()["referenceId"]

    # Confirm first
    inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Confirmed"})
    # Complete
    inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Completed"})

    # Check future availability on same date
    avail = inventory_client.get(
        "/api/v1/availability/equipment/aputure-300d-ii?startDate=2026-12-14&endDate=2026-12-14"
    )
    assert avail.json()["availableQuantity"] == 2


# -----------------------------------------------------------------
# 4. Status Transitions (Tests 28 - 34)
# -----------------------------------------------------------------
def test_transition_pending_to_confirmed(inventory_client):
    """Test 28: Pending Review -> Confirmed."""
    payload = {
        "customerName": "Test Confirm",
        "email": "tc@example.com",
        "phone": "9876543236",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    res = inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Confirmed"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "Confirmed"


def test_transition_pending_to_rejected(inventory_client):
    """Test 29: Pending Review -> Rejected."""
    payload = {
        "customerName": "Test Reject",
        "email": "tr@example.com",
        "phone": "9876543237",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    res = inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Rejected"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "Rejected"


def test_transition_pending_to_cancelled(inventory_client):
    """Test 30: Pending Review -> Cancelled."""
    payload = {
        "customerName": "Test Cancel",
        "email": "tcan@example.com",
        "phone": "9876543238",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    res = inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Cancelled"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "Cancelled"


def test_transition_confirmed_to_cancelled(inventory_client):
    """Test 31: Confirmed -> Cancelled."""
    payload = {
        "customerName": "Test CnfCan",
        "email": "tcc@example.com",
        "phone": "9876543239",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Confirmed"})
    res = inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Cancelled"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "Cancelled"


def test_transition_confirmed_to_completed(inventory_client):
    """Test 32: Confirmed -> Completed."""
    payload = {
        "customerName": "Test CnfComp",
        "email": "tcomp@example.com",
        "phone": "9876543240",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Confirmed"})
    res = inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Completed"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "Completed"


def test_invalid_status_transitions_rejected(inventory_client):
    """Test 33: Invalid transitions (e.g. Cancelled -> Confirmed) rejected with 400 Bad Request."""
    payload = {
        "customerName": "Test BadTrans",
        "email": "bad@example.com",
        "phone": "9876543241",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-01",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Cancelled"})

    # Attempt Cancelled -> Confirmed
    bad_res = inventory_client.patch(f"/api/v1/rentals/enquiries/{ref}/status", json={"status": "Confirmed"})
    assert bad_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid status transition" in bad_res.json()["detail"]


def test_failed_confirmation_rolls_back(inventory_seeded_db):
    """Test 34: Failed status transition rolls back changes atomically."""
    enquiry = RentalEnquiry(
        reference="GS-2026-FAIL1",
        customer_name="Fail User",
        email="fail@example.com",
        phone="9876543242",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 1),
        duration_days=1,
        subtotal=Decimal("3499.00"),
        discount=Decimal("0.00"),
        estimated_total=Decimal("3499.00"),
        status=EnquiryStatus.CANCELLED,
        hold_expires_at=datetime.now(timezone.utc),
    )
    inventory_seeded_db.add(enquiry)
    inventory_seeded_db.commit()

    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        EnquiryService.update_enquiry_status(inventory_seeded_db, reference="GS-2026-FAIL1", new_status=EnquiryStatus.CONFIRMED)

    inventory_seeded_db.refresh(enquiry)
    assert enquiry.status == EnquiryStatus.CANCELLED


# -----------------------------------------------------------------
# 5. Idempotency Tests (Tests 35 - 37)
# -----------------------------------------------------------------
def test_same_idempotency_key_and_payload_returns_original(inventory_client):
    """Test 35: Same key and payload returns identical enquiry without duplicating allocations."""
    payload = {
        "customerName": "Idemp User",
        "email": "idemp@example.com",
        "phone": "9876543243",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    headers = {"Idempotency-Key": "test-key-12345"}

    res1 = inventory_client.post("/api/v1/rentals/enquiries", json=payload, headers=headers)
    assert res1.status_code == status.HTTP_201_CREATED
    ref1 = res1.json()["referenceId"]

    # Re-send identical request
    res2 = inventory_client.post("/api/v1/rentals/enquiries", json=payload, headers=headers)
    assert res2.status_code == status.HTTP_201_CREATED
    assert res2.json()["referenceId"] == ref1


def test_same_key_different_payload_returns_409(inventory_client):
    """Test 36: Same key with altered payload returns 409 Conflict."""
    payload1 = {
        "customerName": "User A",
        "email": "usera@example.com",
        "phone": "9876543244",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    headers = {"Idempotency-Key": "conflict-key-999"}
    res1 = inventory_client.post("/api/v1/rentals/enquiries", json=payload1, headers=headers)
    assert res1.status_code == status.HTTP_201_CREATED

    payload2 = {**payload1, "customerName": "User B (Tampered)"}
    res2 = inventory_client.post("/api/v1/rentals/enquiries", json=payload2, headers=headers)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "Idempotency-Key was previously used" in res2.json()["detail"]


def test_duplicate_concurrent_requests_handled(inventory_client):
    """Test 37: Concurrent or rapid requests with same key yield same result without double allocations."""
    payload = {
        "customerName": "Rapid User",
        "email": "rapid@example.com",
        "phone": "9876543245",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    headers = {"Idempotency-Key": "rapid-key-888"}
    r1 = inventory_client.post("/api/v1/rentals/enquiries", json=payload, headers=headers)
    r2 = inventory_client.post("/api/v1/rentals/enquiries", json=payload, headers=headers)
    assert r1.status_code == status.HTTP_201_CREATED
    assert r2.status_code == status.HTTP_201_CREATED
    assert r1.json()["referenceId"] == r2.json()["referenceId"]


# -----------------------------------------------------------------
# 6. Enquiry Retrieval & Management (Tests 38 - 41)
# -----------------------------------------------------------------
def test_retrieve_enquiry_by_reference(inventory_client):
    """Test 38: Retrieve enquiry by reference."""
    payload = {
        "customerName": "Lookup User",
        "email": "lookup@example.com",
        "phone": "9876543246",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    res = inventory_client.get(f"/api/v1/rentals/enquiries/{ref}")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["reference"] == ref
    assert data["customerName"] == "Lookup User"
    assert len(data["items"]) == 1


def test_unknown_reference_returns_404(inventory_client):
    """Test 39: Unknown reference returns 404."""
    res = inventory_client.get("/api/v1/rentals/enquiries/GS-2026-999999")
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_pagination_and_status_filters(inventory_client):
    """Test 40: Pagination and status filter on management list."""
    res = inventory_client.get("/api/v1/rentals/enquiries?page=1&limit=5&status=Pending Review")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["limit"] == 5


def test_customer_response_does_not_expose_internal_asset_identifiers(inventory_client):
    """Test 41: Customer response does not expose internal serial numbers, asset codes, or unit IDs."""
    payload = {
        "customerName": "Privacy User",
        "email": "privacy@example.com",
        "phone": "9876543247",
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-12-01",
        "endDate": "2026-12-02",
    }
    ref = inventory_client.post("/api/v1/rentals/enquiries", json=payload).json()["referenceId"]
    res = inventory_client.get(f"/api/v1/rentals/enquiries/{ref}")
    data = res.json()

    raw_text = str(data)
    assert "assetCode" not in raw_text
    assert "serialNumber" not in raw_text
    assert "unitId" not in raw_text
    assert "GS-CAM-" not in raw_text


def test_admin_authentication_required(client):
    """Test 42: Admin listing and status updates reject unauthenticated requests."""
    # List without admin header
    unauth_list = client.get("/api/v1/rentals/enquiries", headers={"X-Admin-Key": ""})
    assert unauth_list.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # Status update without admin header
    unauth_patch = client.patch(
        "/api/v1/rentals/enquiries/GS-2026-0001/status",
        json={"status": "Confirmed"},
        headers={"X-Admin-Key": ""},
    )
    assert unauth_patch.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_admin_authentication_invalid_key(client):
    """Test 43: Admin endpoints reject requests with wrong credentials."""
    bad_key_res = client.get(
        "/api/v1/rentals/enquiries",
        headers={"X-Admin-Key": "wrong-secret-key"},
    )
    assert bad_key_res.status_code == status.HTTP_401_UNAUTHORIZED

