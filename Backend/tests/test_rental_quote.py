from decimal import Decimal
import pytest
from fastapi import status
from sqlalchemy import select

from app.models.catalog import AvailabilityStatus, Equipment, CreatorKitItem


# -----------------------------------------------------------------
# 1. Basic Rental Quote Tests
# -----------------------------------------------------------------
def test_quote_one_product_one_day(seeded_client):
    """Test 1: One product for one day (start == end)."""
    payload = {
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["durationDays"] == 1
    assert len(data["lines"]) == 1
    line = data["lines"][0]
    assert line["id"] == "sony-fx30"
    assert line["type"] == "product"
    assert line["name"] == "Sony FX30"
    assert float(line["dailyRate"]) == 3499.00
    assert line["quantity"] == 1
    assert float(line["subtotal"]) == 3499.00
    assert float(data["total"]) == 3499.00
    assert data["formattedTotal"] == "₹3,499"
    assert data["isProvisional"] is True


def test_quote_one_product_multiple_days(seeded_client):
    """Test 2: One product for multiple days (3 days: Nov 10 to Nov 12)."""
    payload = {
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-12",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["durationDays"] == 3
    # 3499 * 1 * 3 = 10497
    assert float(data["total"]) == 10497.00
    assert data["formattedTotal"] == "₹10,497"


def test_quote_multiple_different_products(seeded_client):
    """Test 3: Multiple different products."""
    payload = {
        "productSelections": [
            {"productId": "sony-fx30", "quantity": 1},  # 3499
            {"productId": "sony-24-70-gm2", "quantity": 1},  # 1899
        ],
        "startDate": "2026-11-10",
        "endDate": "2026-11-11",  # 2 days
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["durationDays"] == 2
    assert len(data["lines"]) == 2
    # Line 1: 3499 * 1 * 2 = 6998
    # Line 2: 1899 * 1 * 2 = 3798
    # Total: 10796
    assert float(data["total"]) == 10796.00
    assert data["formattedTotal"] == "₹10,796"


def test_quote_product_quantity_greater_than_one(seeded_client):
    """Test 4: Product quantity greater than 1."""
    payload = {
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 3}],  # 1999
        "startDate": "2026-11-10",
        "endDate": "2026-11-11",  # 2 days
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["durationDays"] == 2
    line = data["lines"][0]
    assert line["quantity"] == 3
    # 1999 * 3 * 2 = 11994
    assert float(line["subtotal"]) == 11994.00
    assert float(data["total"]) == 11994.00


def test_quote_kit_only(seeded_client):
    """Test 5: Kit-only quote."""
    payload = {
        "kitId": "content-creator-kit",  # 4999
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",  # 1 day
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["durationDays"] == 1
    assert len(data["lines"]) == 1
    line = data["lines"][0]
    assert line["id"] == "content-creator-kit"
    assert line["type"] == "kit"
    assert float(line["dailyRate"]) == 4999.00
    assert len(line["bundledItems"]) == 4
    assert float(data["total"]) == 4999.00


def test_quote_product_only(seeded_client):
    """Test 6: Product-only quote."""
    payload = {
        "productSelections": [{"productId": "nikon-z8", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    assert float(res.json()["total"]) == 4499.00


# -----------------------------------------------------------------
# 2. Kit & Component Deduplication Logic
# -----------------------------------------------------------------
def test_quote_kit_plus_unrelated_products(seeded_client):
    """Test 7: Kit plus unrelated product (both charged)."""
    # Content Creator Kit includes Sony FX30, bi-color ring light, etc.
    # Aputure 300D II is unrelated
    payload = {
        "kitId": "content-creator-kit",  # 4999
        "productSelections": [{"productId": "aputure-300d-ii", "quantity": 1}],  # 1999
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",  # 1 day
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["lines"]) == 2
    # 4999 + 1999 = 6998
    assert float(data["total"]) == 6998.00


def test_quote_kit_plus_included_catalogue_product(seeded_client):
    """Test 8: Kit plus already included catalogue product (qty 1 included, qty 1 requested -> 0 extra charge)."""
    # Content Creator Kit includes 1 Sony FX30
    payload = {
        "kitId": "content-creator-kit",  # 4999
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    # Only the kit line should appear because FX30 is fully covered
    assert len(data["lines"]) == 1
    assert data["lines"][0]["type"] == "kit"
    assert float(data["total"]) == 4999.00


def test_quote_additional_quantity_beyond_kit(seeded_client):
    """Test 9: Additional quantity beyond kit-included quantity (1 included, 3 requested -> charge 2)."""
    payload = {
        "kitId": "content-creator-kit",  # 4999
        "productSelections": [{"productId": "sony-fx30", "quantity": 3}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",  # 1 day
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["lines"]) == 2
    prod_line = next(line for line in data["lines"] if line["type"] == "product")
    assert prod_line["id"] == "sony-fx30"
    assert prod_line["quantity"] == 2  # 3 requested - 1 included = 2
    # Kit: 4999 + FX30: 2 * 3499 = 4999 + 6998 = 11997
    assert float(data["total"]) == 11997.00


def test_multiple_kit_components_and_included_quantities(seeded_db, seeded_client):
    """Test 10: Kit with multiple catalogue-linked components."""
    # Let's add an explicit link to sony-24-70-gm2 in Content Creator Kit
    fx30 = seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-fx30"))
    lens = seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-24-70-gm2"))
    kit = seeded_db.scalar(select(Equipment).where(Equipment.product_id == "content-creator-kit")) # or CreatorKit

    # Add second linked item to content-creator-kit in DB
    from app.models.catalog import CreatorKit
    c_kit = seeded_db.scalar(select(CreatorKit).where(CreatorKit.kit_id == "content-creator-kit"))
    new_item = CreatorKitItem(
        kit_id=c_kit.id,
        role="Primary Lens",
        name="Sony FE 24-70mm GM II",
        equipment_id=lens.id,
        quantity=2,  # 2 lenses included
        sort_order=5,
    )
    seeded_db.add(new_item)
    seeded_db.commit()

    # Request 3 lenses (so 3 - 2 = 1 chargeable) and 1 FX30 (1 - 1 = 0 chargeable)
    payload = {
        "kitId": "content-creator-kit",  # 4999
        "productSelections": [
            {"productId": "sony-fx30", "quantity": 1},
            {"productId": "sony-24-70-gm2", "quantity": 3},
        ],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["lines"]) == 2  # Kit + 1 Lens
    lens_line = next(line for line in data["lines"] if line["id"] == "sony-24-70-gm2")
    assert lens_line["quantity"] == 1
    # Kit: 4999 + Lens: 1899 = 6898
    assert float(data["total"]) == 6898.00


# -----------------------------------------------------------------
# 3. Availability Status Resilience (Low Stock & Reserved allowed)
# -----------------------------------------------------------------
def test_quote_low_stock_product(seeded_db, seeded_client):
    """Test 11: Low Stock product quote succeeds."""
    item = seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-fx30"))
    item.availability = AvailabilityStatus.LOW_STOCK
    seeded_db.commit()

    payload = {
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    assert float(res.json()["total"]) == 3499.00


def test_quote_reserved_product(seeded_db, seeded_client):
    """Test 12: Reserved product quote succeeds."""
    item = seeded_db.scalar(select(Equipment).where(Equipment.product_id == "sony-a7-iv"))
    item.availability = AvailabilityStatus.RESERVED
    seeded_db.commit()

    payload = {
        "productSelections": [{"productId": "sony-a7-iv", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    assert float(res.json()["total"]) == 2999.00


# -----------------------------------------------------------------
# 4. Error Handling & Validation
# -----------------------------------------------------------------
def test_quote_invalid_dates(seeded_client):
    """Test 13: Invalid dates format rejected."""
    payload = {
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "invalid-date",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_quote_end_date_earlier_than_start_date(seeded_client):
    """Test 14: End date earlier than start date rejected."""
    payload = {
        "productSelections": [{"productId": "sony-fx30", "quantity": 1}],
        "startDate": "2026-11-15",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_quote_unknown_product(seeded_client):
    """Test 15: Unknown product returns 404."""
    payload = {
        "productSelections": [{"productId": "unknown-nonexistent-camera", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_quote_inactive_product(seeded_db, seeded_client):
    """Test 16: Inactive product returns 400 Bad Request."""
    item = seeded_db.scalar(select(Equipment).where(Equipment.product_id == "nikon-z8"))
    item.is_active = False
    seeded_db.commit()

    payload = {
        "productSelections": [{"productId": "nikon-z8", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_quote_non_rentable_product(seeded_client, seeded_db):
    """Test 17: Explicitly unrentable product returns 400, while all catalogue products default to rentable."""
    from app.models.catalog import Equipment
    eq = seeded_db.query(Equipment).filter(Equipment.product_id == "vintage-camera-strap").first()
    eq.is_rentable = False
    seeded_db.commit()

    payload = {
        "productSelections": [{"productId": "vintage-camera-strap", "quantity": 1}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_quote_unknown_kit(seeded_client):
    """Test 18: Unknown kit returns 404."""
    payload = {
        "kitId": "nonexistent-kit",
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_quote_invalid_quantity(seeded_client):
    """Test 19: Quantity 0 or negative rejected."""
    payload = {
        "productSelections": [{"productId": "sony-fx30", "quantity": 0}],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_quote_duplicate_product_selections(seeded_client):
    """Test 20: Duplicate product selections rejected."""
    payload = {
        "productSelections": [
            {"productId": "sony-fx30", "quantity": 1},
            {"productId": "sony-fx30", "quantity": 2},
        ],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_quote_empty_selection(seeded_client):
    """Test 21: Empty selection (no product and no kit) rejected."""
    payload = {
        "productSelections": [],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_decimal_precision_and_inr_formatting(seeded_client):
    """Test 22: Large amounts maintain decimal precision and traditional INR number grouping."""
    payload = {
        "productSelections": [
            {"productId": "nikon-z8", "quantity": 10},  # 4499 * 10 = 44,990 / day
        ],
        "startDate": "2026-11-01",
        "endDate": "2026-11-10",  # 10 days -> 4,49,900
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert float(data["total"]) == 449900.00
    assert data["formattedTotal"] == "₹4,49,900"


def test_reject_client_provided_price(seeded_client):
    """Reject requests with client-supplied price tampering."""
    payload = {
        "productSelections": [
            {"productId": "sony-fx30", "quantity": 1, "price": 10.00}
        ],
        "startDate": "2026-11-10",
        "endDate": "2026-11-10",
    }
    res = seeded_client.post("/api/v1/rentals/quote", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
