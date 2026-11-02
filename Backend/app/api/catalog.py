from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.catalog import AvailabilityStatus
from app.schemas.catalog import (
    CategoryResponse,
    CreatorKitResponse,
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
    PaginatedResponse,
)
from app.services.catalog_service import CatalogService

router = APIRouter()


# -------------------------------------------------------------
# Categories Endpoints
# -------------------------------------------------------------
@router.get(
    "/categories",
    response_model=List[CategoryResponse],
    summary="List all categories",
    description="Returns all active equipment categories along with live counts of active products in each category.",
    tags=["Categories"],
)
def list_categories(
    active_only: bool = Query(True, description="Filter active categories only"),
    db: Session = Depends(get_db),
):
    return CatalogService.get_categories(db=db, active_only=active_only)


@router.get(
    "/categories/{slug}",
    response_model=CategoryResponse,
    summary="Get category details by slug",
    description="Returns detailed metadata and dynamic product count for a specific category.",
    tags=["Categories"],
)
def get_category(
    slug: str,
    db: Session = Depends(get_db),
):
    return CatalogService.get_category_by_slug(db=db, slug=slug)


# -------------------------------------------------------------
# Equipment Endpoints
# -------------------------------------------------------------
@router.get(
    "/equipment",
    response_model=PaginatedResponse[EquipmentResponse],
    summary="List equipment with filtering, search, and pagination",
    description="Returns paginated equipment catalog filtered by category, brand, availability, featured status, or rentable calculator status.",
    tags=["Equipment"],
)
def list_equipment(
    category: Optional[str] = Query(None, description="Filter by category slug or name"),
    search: Optional[str] = Query(None, description="Search term matching name, brand, description, or spec"),
    brand: Optional[str] = Query(None, description="Filter by brand name (e.g. 'Sony', 'Canon', 'DJI')"),
    availability: Optional[AvailabilityStatus] = Query(None, description="Filter by availability status ('Available', 'Low Stock', 'Reserved')"),
    featured: Optional[bool] = Query(None, description="Filter by featured status (Section 02)"),
    rentable: Optional[bool] = Query(None, description="Filter by rental calculator status"),
    sort_by: Optional[str] = Query(
        "name_asc",
        description="Sort by field: 'price_asc', 'price_desc', 'name_asc', or 'newest'",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(12, ge=1, le=100, description="Page size (max 100)"),
    active_only: bool = Query(True, description="Filter active equipment only"),
    db: Session = Depends(get_db),
):
    return CatalogService.get_equipment_list(
        db=db,
        category=category,
        search=search,
        brand=brand,
        availability=availability,
        featured=featured,
        rentable=rentable,
        sort_by=sort_by,
        page=page,
        limit=limit,
        active_only=active_only,
    )


@router.get(
    "/equipment/{product_id}",
    response_model=EquipmentResponse,
    summary="Get equipment by product ID",
    description="Retrieve full equipment product specifications and pricing by its unique product slug.",
    tags=["Equipment"],
)
def get_equipment_detail(
    product_id: str,
    db: Session = Depends(get_db),
):
    return CatalogService.get_equipment_by_id(db=db, product_id=product_id)


@router.post(
    "/equipment",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create equipment",
    description="Add a new equipment product to the catalogue.",
    tags=["Equipment"],
)
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
):
    return CatalogService.create_equipment(db=db, data=payload)


@router.put(
    "/equipment/{product_id}",
    response_model=EquipmentResponse,
    summary="Update equipment",
    description="Update existing equipment details.",
    tags=["Equipment"],
)
def update_equipment(
    product_id: str,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
):
    return CatalogService.update_equipment(db=db, product_id=product_id, data=payload)


@router.delete(
    "/equipment/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete equipment",
    description="Delete an equipment item from the catalogue.",
    tags=["Equipment"],
)
def delete_equipment(
    product_id: str,
    db: Session = Depends(get_db),
):
    CatalogService.delete_equipment(db=db, product_id=product_id)
    return None


# -------------------------------------------------------------
# Creator Kits Endpoints
# -------------------------------------------------------------
@router.get(
    "/kits",
    response_model=List[CreatorKitResponse],
    summary="List Creator Kits",
    description="Retrieve all curated Creator Kits with their bundled components.",
    tags=["Creator Kits"],
)
def list_creator_kits(
    active_only: bool = Query(True, description="Filter active kits only"),
    db: Session = Depends(get_db),
):
    return CatalogService.get_creator_kits(db=db, active_only=active_only)


@router.get(
    "/kits/{kit_id}",
    response_model=CreatorKitResponse,
    summary="Get Creator Kit details",
    description="Retrieve full details and bundled item specifications for a Creator Kit.",
    tags=["Creator Kits"],
)
def get_creator_kit_detail(
    kit_id: str,
    db: Session = Depends(get_db),
):
    return CatalogService.get_creator_kit_by_id(db=db, kit_id=kit_id)
