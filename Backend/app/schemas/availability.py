from datetime import date
from typing import List, Optional
from pydantic import ConfigDict, Field, field_validator, model_validator

from app.schemas.catalog import CamelModel


class ProductSelectionItem(CamelModel):
    product_id: str = Field(..., alias="productId", min_length=1, description="Catalogue product ID")
    quantity: int = Field(1, ge=1, description="Quantity must be >= 1")

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=CamelModel.model_config["alias_generator"],
        populate_by_name=True,
    )


class ProductAvailabilityResponse(CamelModel):
    product_id: str = Field(..., alias="productId")
    product_name: str = Field(..., alias="productName")
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")
    total_active_units: int = Field(..., alias="totalActiveUnits")
    available_quantity: int = Field(..., alias="availableQuantity")
    requested_quantity: int = Field(..., alias="requestedQuantity")
    is_available: bool = Field(..., alias="isAvailable")
    available_asset_codes: Optional[List[str]] = Field(None, alias="availableAssetCodes")


class KitComponentAvailability(CamelModel):
    role: str
    name: str
    product_id: Optional[str] = Field(None, alias="productId")
    is_catalogue_linked: bool = Field(..., alias="isCatalogueLinked")
    required_quantity: int = Field(..., alias="requiredQuantity")
    available_quantity: Optional[int] = Field(None, alias="availableQuantity")
    is_available: bool = Field(..., alias="isAvailable")
    reason: Optional[str] = None


class KitAvailabilityResponse(CamelModel):
    kit_id: str = Field(..., alias="kitId")
    kit_title: str = Field(..., alias="kitTitle")
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")
    requested_quantity: int = Field(..., alias="requestedQuantity")
    is_available: bool = Field(..., alias="isAvailable")
    components: List[KitComponentAvailability]


class CombinedAvailabilityCheckRequest(CamelModel):
    product_selections: List[ProductSelectionItem] = Field(
        default_factory=list,
        alias="productSelections",
        description="Individual catalogue product selections",
    )
    kit_id: Optional[str] = Field(
        None,
        alias="kitId",
        description="Optional Creator Kit ID to check",
    )
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=CamelModel.model_config["alias_generator"],
        populate_by_name=True,
    )

    @field_validator("kit_id")
    @classmethod
    def validate_kit_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @model_validator(mode="after")
    def validate_request(self) -> "CombinedAvailabilityCheckRequest":
        if self.end_date < self.start_date:
            raise ValueError("endDate cannot be earlier than startDate")
        if not self.product_selections and not self.kit_id:
            raise ValueError("At least one product selection or a Creator Kit must be provided")

        seen_ids = set()
        for item in self.product_selections:
            pid = item.product_id.strip()
            if pid in seen_ids:
                raise ValueError(f"Duplicate product selection '{pid}' is not allowed")
            seen_ids.add(pid)

        return self


class ProductAvailabilityReport(CamelModel):
    product_id: str = Field(..., alias="productId")
    product_name: str = Field(..., alias="productName")
    requested_quantity: int = Field(..., alias="requestedQuantity")
    available_quantity: int = Field(..., alias="availableQuantity")
    is_available: bool = Field(..., alias="isAvailable")
    reason: Optional[str] = None


class CombinedAvailabilityCheckResponse(CamelModel):
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")
    is_available: bool = Field(..., alias="isAvailable")
    products: List[ProductAvailabilityReport]
    kit: Optional[KitAvailabilityResponse] = None
