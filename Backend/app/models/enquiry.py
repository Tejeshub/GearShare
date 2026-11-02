import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
import enum

if TYPE_CHECKING:
    from app.models.inventory import RentalAllocation

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnquiryStatus(str, enum.Enum):
    PENDING_REVIEW = "Pending Review"
    CONFIRMED = "Confirmed"
    REJECTED = "Rejected"
    EXPIRED = "Expired"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class RentalEnquiry(Base):
    __tablename__ = "rental_enquiries"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    reference: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=Decimal("0.00"), nullable=False
    )
    estimated_total: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )

    status: Mapped[EnquiryStatus] = mapped_column(
        Enum(EnquiryStatus, native_enum=False, length=50),
        default=EnquiryStatus.PENDING_REVIEW,
        index=True,
        nullable=False,
    )

    # Temporary 24-hour hold expiry
    hold_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    # Email notification tracking
    confirmation_email_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    confirmation_email_error: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    confirmation_email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    items: Mapped[List["RentalEnquiryItem"]] = relationship(
        "RentalEnquiryItem",
        back_populates="enquiry",
        cascade="all, delete-orphan",
        order_by="RentalEnquiryItem.created_at",
    )
    allocations: Mapped[List["RentalAllocation"]] = relationship(
        "RentalAllocation",
        back_populates="enquiry",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_rental_enquiries_status_hold", "status", "hold_expires_at"),
    )

    def __repr__(self) -> str:
        return f"<RentalEnquiry {self.reference} ({self.status.value})>"


class RentalEnquiryItem(Base):
    __tablename__ = "rental_enquiry_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    enquiry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rental_enquiries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "product" or "kit"
    equipment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("equipment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("creator_kits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Historical snapshots
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    daily_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )

    # Snapshot of bundled kit components for historical accuracy
    bundled_components_snapshot: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    enquiry: Mapped["RentalEnquiry"] = relationship(
        "RentalEnquiry", back_populates="items"
    )

    def __repr__(self) -> str:
        return f"<RentalEnquiryItem {self.item_type} - {self.name} (qty {self.quantity})>"


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    enquiry_reference: Mapped[str] = mapped_column(String(50), nullable=False)
    response_data: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<IdempotencyRecord {self.key} -> {self.enquiry_reference}>"
