from decimal import Decimal
import pytest
from fastapi import status
from sqlalchemy import select

from app.db.seed import seed_database
from app.models.catalog import Category, Equipment, CreatorKit


# -----------------------------------------------------------------
# 1. Seeding and Idempotency Tests
# -----------------------------------------------------------------
def test_seed_idempotency(db_session):
    """Verify running seed script multiple times is strictly idempotent."""
    counts_run1 = seed_database(db_session)
    assert counts_run1["categories"] == 8
    assert counts_run1["equipment"] == 12
    assert counts_run1["kits"] == 3
    assert counts_run1["kit_items"] == 12

    # Run seed second time
    counts_run2 = seed_database(db_session)
    assert counts_run2 == counts_run1

    # Verify database counts
    total_categories = db_session.scalar(select(Category).count()) if hasattr(select(Category), "count") else len(db_session.scalars(select(Category)).all())
    total_equipment = len(db_session.scalars(select(Equipment)).all())
    total_kits = len(db_session.scalars(select(CreatorKit)).all())

    assert total_categories == 8
    assert total_equipment == 12
    assert total_kits == 3


# -----------------------------------------------------------------
# 2. Categories API Tests
# -----------------------------------------------------------------
def test_list_categories(seeded_client):
    """Test listing all categories with active product counts."""
    res = seeded_client.get("/api/v1/categories")
    assert res.status_code == status.HTTP_200_OK
    categories = res.json()
    assert len(categories) == 8

    # Check structure
    cat_names = [c["name"] for c in categories]
    assert "Cameras" in cat_names
    assert "Lenses" in cat_names
    assert "Lighting" in cat_names
    assert "Stabilization" in cat_names
    assert "Car Mount" in cat_names
    assert "Camera Strap" in cat_names
    assert "Tripod" in cat_names
    assert "Gimbal" in cat_names

    # Check dynamic product count on Cameras (FX30, A7 IV, R6 II, Z8 = 4)
    cameras_cat = next(c for c in categories if c["slug"] == "cameras")
    assert cameras_cat["productCount"] == 4


def test_get_category_by_slug(seeded_client):
    """Test retrieving single category by slug."""
    res = seeded_client.get("/api/v1/categories/cameras")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["name"] == "Cameras"
    assert data["slug"] == "cameras"
    assert data["productCount"] == 4


def test_get_category_not_found(seeded_client):
    """Test 404 on nonexistent category."""
    res = seeded_client.get("/api/v1/categories/nonexistent-category")
    assert res.status_code == status.HTTP_404_NOT_FOUND


# -----------------------------------------------------------------
# 3. Equipment Listing, Pagination, and Filter Tests
# -----------------------------------------------------------------
def test_equipment_listing_and_pagination(seeded_client):
    """Test equipment list with default pagination and pagination limits."""
    # Default page=1, limit=12
    res = seeded_client.get("/api/v1/equipment")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 12
    assert len(data["items"]) == 12
    assert data["page"] == 1
    assert data["limit"] == 12
    assert data["totalPages"] == 1

    # Custom limit pagination
    res_paged = seeded_client.get("/api/v1/equipment?page=1&limit=5")
    assert res_paged.status_code == status.HTTP_200_OK
    paged_data = res_paged.json()
    assert paged_data["total"] == 12
    assert len(paged_data["items"]) == 5
    assert paged_data["totalPages"] == 3


def test_equipment_filter_by_category(seeded_client):
    """Filter equipment by category name or slug."""
    # Filter by slug
    res = seeded_client.get("/api/v1/equipment?category=cameras")
    assert res.status_code == status.HTTP_200_OK
    items = res.json()["items"]
    assert len(items) == 4
    for item in items:
        assert item["category"] == "Cameras"

    # Filter by category name
    res_name = seeded_client.get("/api/v1/equipment?category=Lenses")
    assert res_name.status_code == status.HTTP_200_OK
    items_name = res_name.json()["items"]
    assert len(items_name) == 2


def test_equipment_filter_by_brand(seeded_client):
    """Filter equipment by brand."""
    res = seeded_client.get("/api/v1/equipment?brand=Sony")
    assert res.status_code == status.HTTP_200_OK
    items = res.json()["items"]
    # Sony FX30, Sony A7 IV, Sony 24-70 GM II, Sony 70-200 GM II
    assert len(items) == 4
    for item in items:
        assert item["brand"] == "Sony"


def test_equipment_filter_by_availability(seeded_client):
    """Filter equipment by availability enum."""
    res = seeded_client.get("/api/v1/equipment?availability=Available")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == 12


def test_equipment_filter_featured_and_rentable(seeded_client):
    """Filter featured (Section 02) and rentable (Calculator) items."""
    # Featured items
    res_featured = seeded_client.get("/api/v1/equipment?featured=true")
    assert res_featured.status_code == status.HTTP_200_OK
    # 8 featured items in finalizedProducts
    assert res_featured.json()["total"] == 8

    # Rentable items (All 12 catalogue products are now individually rentable)
    res_rentable = seeded_client.get("/api/v1/equipment?rentable=true")
    assert res_rentable.status_code == status.HTTP_200_OK
    assert res_rentable.json()["total"] == 12


def test_equipment_search(seeded_client):
    """Search equipment across name, brand, spec, and description."""
    res = seeded_client.get("/api/v1/equipment?search=stabilizer")
    assert res.status_code == status.HTTP_200_OK
    items = res.json()["items"]
    # Matches DJI RS 4 Pro and DJI RS3 Pro stabilizer descriptions
    assert len(items) == 2
    item_ids = [item["id"] for item in items]
    assert "dji-rs4-pro" in item_ids
    assert "dji-rs3-pro" in item_ids


def test_equipment_sorting(seeded_client):
    """Test price ascending and descending sort."""
    # Price ascending
    res_asc = seeded_client.get("/api/v1/equipment?sort_by=price_asc")
    assert res_asc.status_code == status.HTTP_200_OK
    prices_asc = [float(item["price"]) for item in res_asc.json()["items"]]
    assert prices_asc == sorted(prices_asc)

    # Price descending
    res_desc = seeded_client.get("/api/v1/equipment?sort_by=price_desc")
    assert res_desc.status_code == status.HTTP_200_OK
    prices_desc = [float(item["price"]) for item in res_desc.json()["items"]]
    assert prices_desc == sorted(prices_desc, reverse=True)


# -----------------------------------------------------------------
# 4. Equipment Detail & CRUD Operations
# -----------------------------------------------------------------
def test_get_equipment_by_id(seeded_client):
    """Retrieve equipment by product ID."""
    res = seeded_client.get("/api/v1/equipment/sony-fx30")
    assert res.status_code == status.HTTP_200_OK
    item = res.json()
    assert item["id"] == "sony-fx30"
    assert item["name"] == "Sony FX30"
    assert item["brand"] == "Sony"
    assert item["category"] == "Cameras"
    assert float(item["price"]) == 3499.00
    assert len(item["specs"]) == 4


def test_get_equipment_not_found(seeded_client):
    """Retrieve nonexistent equipment returns 404."""
    res = seeded_client.get("/api/v1/equipment/nonexistent-item")
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_create_equipment(seeded_client):
    """Create equipment and verify validation."""
    new_item = {
        "id": "blackmagic-6k-pro",
        "name": "Blackmagic Pocket Cinema 6K Pro",
        "brand": "Blackmagic",
        "category": "Cameras",
        "description": "High-end handheld 6K digital film camera.",
        "image": "/images/products/bmpcc6k.jpg",
        "spec": "6K Super 35 · EF Mount · Built-in NDs",
        "specs": ["6144 x 3456 Super 35 sensor", "Gen 5 Color Science"],
        "price": 2899.00,
        "availability": "Available",
        "isFeatured": False,
        "isRentable": True,
        "isActive": True,
    }
    res = seeded_client.post("/api/v1/equipment", json=new_item)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["id"] == "blackmagic-6k-pro"
    assert data["category"] == "Cameras"

    # Test duplicate ID conflict 409
    dup_res = seeded_client.post("/api/v1/equipment", json=new_item)
    assert dup_res.status_code == status.HTTP_409_CONFLICT


def test_update_equipment(seeded_client):
    """Update equipment attributes."""
    update_data = {
        "price": 3699.00,
        "availability": "Low Stock",
    }
    res = seeded_client.put("/api/v1/equipment/sony-fx30", json=update_data)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert float(data["price"]) == 3699.00
    assert data["availability"] == "Low Stock"


def test_delete_equipment(seeded_client):
    """Delete equipment and verify 404 on subsequent get."""
    res = seeded_client.delete("/api/v1/equipment/vintage-camera-strap")
    assert res.status_code == status.HTTP_204_NO_CONTENT

    # Verify not found
    get_res = seeded_client.get("/api/v1/equipment/vintage-camera-strap")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


# -----------------------------------------------------------------
# 5. Creator Kits API Tests
# -----------------------------------------------------------------
def test_list_creator_kits(seeded_client):
    """Test listing all 3 Creator Kits with bundled items."""
    res = seeded_client.get("/api/v1/kits")
    assert res.status_code == status.HTTP_200_OK
    kits = res.json()
    assert len(kits) == 3

    kit_ids = [k["id"] for k in kits]
    assert "insta360-luna-ultra" in kit_ids
    assert "content-creator-kit" in kit_ids
    assert "canon-content-creator" in kit_ids

    # Verify Content Creator Kit has 4 included items and linked Sony FX30
    content_kit = next(k for k in kits if k["id"] == "content-creator-kit")
    assert len(content_kit["includedItems"]) == 4
    assert float(content_kit["price"]) == 4999.00
    assert "sony-fx30" in content_kit["productIds"]


def test_get_creator_kit_by_id(seeded_client):
    """Test retrieving single Creator Kit by ID."""
    res = seeded_client.get("/api/v1/kits/insta360-luna-ultra")
    assert res.status_code == status.HTTP_200_OK
    kit = res.json()
    assert kit["id"] == "insta360-luna-ultra"
    assert kit["title"] == "Insta360 Luna Ultra Creator Bundle"
    assert float(kit["price"]) == 3899.00
    assert len(kit["includedItems"]) == 4


def test_get_creator_kit_not_found(seeded_client):
    """Test 404 for unknown creator kit."""
    res = seeded_client.get("/api/v1/kits/unknown-bundle")
    assert res.status_code == status.HTTP_404_NOT_FOUND
