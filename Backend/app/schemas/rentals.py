from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import ConfigDict, Field, field_validator, model_validator

from app.schemas.catalog import CamelModel


class RentalSelectionItem(CamelModel):
    product_id: str = Field(..., alias="productId", min_length=1, description="Catalogue product ID")
    quantity: int = Field(..., ge=1, description="Quantity must be a positive integer >= 1")

    # Extra fields like client-provided 'price' are strictly forbidden
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=CamelModel.model_config["alias_generator"],
        populate_by_name=True,
    )


class RentalQuoteRequest(CamelModel):
    product_selections: List[RentalSelectionItem] = Field(
        default_factory=list,
        alias="productSelections",
        description="List of selected products and quantities",
    )
    kit_id: Optional[str] = Field(
        None,
        alias="kitId",
        description="Optional Creator Kit ID to bundle",
    )
    start_date: date = Field(
        ...,
        alias="startDate",
        description="Rental start date (YYYY-MM-DD)",
    )
    end_date: date = Field(
        ...,
        alias="endDate",
        description="Rental end date (YYYY-MM-DD)",
    )

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
    def validate_dates_and_selections(self) -> "RentalQuoteRequest":
        # 1. Validate date range: end_date must not be earlier than start_date
        if self.end_date < self.start_date:
            raise ValueError("endDate cannot be earlier than startDate")

        # 2. Validate empty selection: must provide at least one product selection or a kit_id
        if not self.product_selections and not self.kit_id:
            raise ValueError("At least one product selection or a Creator Kit must be provided")

        # 3. Check for duplicate product IDs in product_selections
        seen_ids = set()
        for item in self.product_selections:
            pid = item.product_id.strip()
            if pid in seen_ids:
                raise ValueError(f"Duplicate product selection '{pid}' is not allowed")
            seen_ids.add(pid)

        return self


class BundledItemInfo(CamelModel):
    role: str
    name: str
    quantity: int
    product_id: Optional[str] = Field(None, alias="productId")


class ItemizedQuoteLine(CamelModel):
    id: str = Field(..., description="Product ID or Kit ID")
    type: Literal["product", "kit"] = Field(..., description="Line item type")
    name: str = Field(..., description="Display name of the equipment or kit")
    brand: Optional[str] = Field(None, description="Brand name for products")
    daily_rate: Decimal = Field(..., alias="dailyRate", description="Daily rate in INR")
    quantity: int = Field(..., description="Chargeable quantity")
    duration_days: int = Field(..., alias="durationDays", description="Rental period in calendar days")
    subtotal: Decimal = Field(..., description="Line subtotal: dailyRate * quantity * durationDays")
    # Additional helpful metadata without breaking frontend contracts
    bundled_items: Optional[List[BundledItemInfo]] = Field(
        None,
        alias="bundledItems",
        description="Bundled items description if line is a creator kit",
    )


class RentalQuoteResponse(CamelModel):
    lines: List[ItemizedQuoteLine]
    duration_days: int = Field(..., alias="durationDays")
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    is_provisional: bool = Field(True, alias="isProvisional")
    formatted_total: str = Field(..., alias="formattedTotal")
