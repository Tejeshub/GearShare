import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional
from pydantic import ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.enquiry import EnquiryStatus
from app.schemas.catalog import CamelModel
from app.schemas.rentals import ItemizedQuoteLine, RentalQuoteResponse, RentalSelectionItem


class EnquirySubmissionPayload(CamelModel):
    customer_name: str = Field(..., alias="customerName", min_length=2, max_length=200)
    email: EmailStr = Field(..., description="Valid customer email address")
    phone: str = Field(
        ...,
        description="Customer Indian mobile phone number (10 digits starting with 6-9)",
    )
    message: Optional[str] = Field(None, max_length=2000)

    product_selections: List[RentalSelectionItem] = Field(
        default_factory=list,
        alias="productSelections",
        description="Individual catalogue product selections",
    )
    kit_id: Optional[str] = Field(
        None,
        alias="kitId",
        description="Optional Creator Kit ID to bundle",
    )
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")

    # Informational client fields from frontend contract (never trusted for actual calculations)
    duration_days: Optional[int] = Field(None, alias="durationDays")
    calculated_estimate: Optional[Decimal] = Field(None, alias="calculatedEstimate")

    model_config = ConfigDict(
        extra="ignore",  # Ignore extra client fields gracefully
        alias_generator=CamelModel.model_config["alias_generator"],
        populate_by_name=True,
    )

    @field_validator("customer_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("customerName must be at least 2 characters")
        return cleaned

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> str:
        if not isinstance(v, str):
            v = str(v)
        cleaned = v.strip()
        # If client passed "+91" prefix, strip it gracefully
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:].strip()
        elif cleaned.startswith("91") and len(cleaned) == 12:
            cleaned = cleaned[2:].strip()
        elif cleaned.startswith("0") and len(cleaned) == 11:
            cleaned = cleaned[1:].strip()
        # Remove any internal hyphens or spaces
        cleaned = re.sub(r"[\s\-]", "", cleaned)

        # Strict Indian mobile number: exactly 10 digits starting with 6, 7, 8, or 9
        if not re.match(r"^[6-9]\d{9}$", cleaned):
            raise ValueError("phone must be a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9")
        return cleaned

    @field_validator("kit_id")
    @classmethod
    def validate_kit_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @model_validator(mode="after")
    def validate_request_logic(self) -> "EnquirySubmissionPayload":
        if self.end_date < self.start_date:
            raise ValueError("endDate cannot be earlier than startDate")
        if not self.product_selections and not self.kit_id:
            raise ValueError("At least one product selection or a Creator Kit must be provided")

        seen = set()
        for p in self.product_selections:
            pid = p.product_id.strip()
            if pid in seen:
                raise ValueError(f"Duplicate product selection '{pid}' is not allowed")
            seen.add(pid)
        return self


class EnquirySubmissionResult(CamelModel):
    success: bool
    reference_id: str = Field(..., alias="referenceId")
    is_simulated: bool = Field(False, alias="isSimulated")
    message: str
    status: EnquiryStatus
    hold_expires_at: datetime = Field(..., alias="holdExpiresAt")
    quote: RentalQuoteResponse
    confirmation_email_sent: bool = Field(False, alias="confirmationEmailSent")


class EnquiryItemDetail(CamelModel):
    id: uuid.UUID
    item_type: str = Field(..., alias="itemType")
    name: str
    brand: Optional[str] = None
    daily_rate: Decimal = Field(..., alias="dailyRate")
    quantity: int
    duration_days: int = Field(..., alias="durationDays")
    subtotal: Decimal
    bundled_components: Optional[List[dict]] = Field(None, alias="bundledComponents")


class RentalEnquiryDetail(CamelModel):
    id: uuid.UUID
    reference: str
    customer_name: str = Field(..., alias="customerName")
    email: str
    phone: str
    message: Optional[str] = None
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")
    duration_days: int = Field(..., alias="durationDays")
    subtotal: Decimal
    discount: Decimal
    estimated_total: Decimal = Field(..., alias="estimatedTotal")
    status: EnquiryStatus
    hold_expires_at: datetime = Field(..., alias="holdExpiresAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    items: List[EnquiryItemDetail] = Field(default_factory=list)


class UpdateEnquiryStatusRequest(CamelModel):
    status: EnquiryStatus = Field(..., description="Target status transition")
