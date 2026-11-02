import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import enum

if TYPE_CHECKING:
    from app.models.catalog import Equipment
    from app.models.enquiry import RentalEnquiry

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UnitCondition(str, enum.Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    DAMAGED = "Damaged"


class UnitOperationalStatus(str, enum.Enum):
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    RETIRED = "Retired"


class AllocationStatus(str, enum.Enum):
    RESERVED = "Reserved"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class EquipmentUnit(Base):
    __tablename__ = "equipment_units"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    condition: Mapped[UnitCondition] = mapped_column(
        Enum(UnitCondition, native_enum=False, length=50),
        default=UnitCondition.EXCELLENT,
        nullable=False,
    )
    operational_status: Mapped[UnitOperationalStatus] = mapped_column(
        Enum(UnitOperationalStatus, native_enum=False, length=50),
        default=UnitOperationalStatus.ACTIVE,
        index=True,
        nullable=False,
    )
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="units")
    allocations: Mapped[List["RentalAllocation"]] = relationship(
        "RentalAllocation", back_populates="unit", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_equipment_units_equipment_status", "equipment_id", "operational_status"),
    )

    def __repr__(self) -> str:
        return f"<EquipmentUnit {self.asset_code} ({self.operational_status.value})>"


class RentalAllocation(Base):
    __tablename__ = "rental_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[AllocationStatus] = mapped_column(
        Enum(AllocationStatus, native_enum=False, length=50),
        default=AllocationStatus.RESERVED,
        index=True,
        nullable=False,
    )
    enquiry_reference: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    enquiry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("rental_enquiries.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    unit: Mapped["EquipmentUnit"] = relationship("EquipmentUnit", back_populates="allocations")
    enquiry: Mapped[Optional["RentalEnquiry"]] = relationship(
        "RentalEnquiry", back_populates="allocations"
    )

    __table_args__ = (
        Index("ix_rental_allocations_dates_status", "unit_id", "start_date", "end_date", "status"),
    )

    def __repr__(self) -> str:
        return f"<RentalAllocation {self.unit_id} [{self.start_date} to {self.end_date}] ({self.status.value})>"
