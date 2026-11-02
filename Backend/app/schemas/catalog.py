import uuid
from datetime import datetime
from decimal import Decimal
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.catalog import AvailabilityStatus

T = TypeVar("T")


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# -------------------------------------------------------------
# Category Schemas
# -------------------------------------------------------------
class CategoryBase(CamelModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    is_visible_in_category_section: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CamelModel):
    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_visible_in_category_section: Optional[bool] = None
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    product_count: int = 0
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------
# Equipment Schemas
# -------------------------------------------------------------
class EquipmentBase(CamelModel):
    id: str = Field(..., alias="id", description="Unique frontend product slug / ID")
    name: str = Field(..., max_length=200)
    brand: str = Field(..., max_length=100)
    category: str = Field(..., description="Category name (e.g. 'Cameras')")
    description: str
    image: str = Field(..., max_length=500)
    spec: str = Field(..., max_length=255)
    specs: List[str] = Field(default_factory=list)
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Daily rental price in INR")
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    is_featured: bool = False
    is_rentable: bool = False
    is_active: bool = True


class EquipmentCreate(CamelModel):
    id: str = Field(..., alias="id", description="Unique product ID slug, e.g. 'sony-fx30'")
    name: str = Field(..., max_length=200)
    brand: str = Field(..., max_length=100)
    category: str = Field(..., description="Category name or slug")
    description: str
    image: str = Field(..., max_length=500)
    spec: str = Field(..., max_length=255)
    specs: List[str] = Field(default_factory=list)
    price: Decimal = Field(..., ge=0)
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    is_featured: bool = False
    is_rentable: bool = False
    is_active: bool = True


class EquipmentUpdate(CamelModel):
    name: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = Field(None, max_length=500)
    spec: Optional[str] = Field(None, max_length=255)
    specs: Optional[List[str]] = None
    price: Optional[Decimal] = Field(None, ge=0)
    availability: Optional[AvailabilityStatus] = None
    is_featured: Optional[bool] = None
    is_rentable: Optional[bool] = None
    is_active: Optional[bool] = None


class EquipmentResponse(EquipmentBase):
    db_id: uuid.UUID = Field(..., alias="dbId")
    category_slug: str = Field(..., alias="categorySlug")
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------
# Creator Kit Schemas
# -------------------------------------------------------------
class CreatorKitItemResponse(CamelModel):
    id: uuid.UUID
    role: str
    name: str
    quantity: int
    sort_order: int
    product_id: Optional[str] = Field(None, alias="productId")


class CreatorKitResponse(CamelModel):
    id: str = Field(..., description="Kit slug identifier e.g. 'content-creator-kit'")
    title: str
    tag: str
    intended_use: str
    description: str
    image: str
    price: Decimal = Field(..., description="Combined daily rental price in INR")
    is_active: bool
    sort_order: int
    included_items: List[CreatorKitItemResponse] = Field(default_factory=list)
    product_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------
# Pagination Generic Schema
# -------------------------------------------------------------
class PaginatedResponse(CamelModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
