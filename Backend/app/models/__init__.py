"""Models package. Export declarative models here for Alembic discovery."""
from app.db.base import Base
from app.models.catalog import (
    AvailabilityStatus,
    Category,
    CreatorKit,
    CreatorKitItem,
    Equipment,
)
from app.models.inventory import (
    AllocationStatus,
    EquipmentUnit,
    RentalAllocation,
    UnitCondition,
    UnitOperationalStatus,
)
from app.models.enquiry import (
    EnquiryStatus,
    IdempotencyRecord,
    RentalEnquiry,
    RentalEnquiryItem,
)
from app.models.contact import ContactMessage

__all__ = [
    "Base",
    "AvailabilityStatus",
    "Category",
    "Equipment",
    "CreatorKit",
    "CreatorKitItem",
    "AllocationStatus",
    "EquipmentUnit",
    "RentalAllocation",
    "UnitCondition",
    "UnitOperationalStatus",
    "EnquiryStatus",
    "RentalEnquiry",
    "RentalEnquiryItem",
    "IdempotencyRecord",
    "ContactMessage",
]
