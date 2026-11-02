import logging
import uuid
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.catalog import CreatorKit, CreatorKitItem, Equipment
from app.models.inventory import (
    AllocationStatus,
    EquipmentUnit,
    RentalAllocation,
    UnitOperationalStatus,
)
from app.models.enquiry import EnquiryStatus, RentalEnquiry
from app.schemas.availability import (
    CombinedAvailabilityCheckRequest,
    CombinedAvailabilityCheckResponse,
    KitAvailabilityResponse,
    KitComponentAvailability,
    ProductAvailabilityReport,
    ProductAvailabilityResponse,
)

logger = logging.getLogger(__name__)


class AvailabilityService:
    @staticmethod
    def get_overlapping_unit_ids(
        db: Session, start_date: date, end_date: date
    ) -> List[uuid.UUID]:
        """
        Returns set of equipment_unit IDs that currently have an active allocation overlapping
        [start_date, end_date] inclusive.
        Takes into account temporary 24-hour hold expiry:
        - Confirmed allocations always block.
        - Reserved allocations with NO linked enquiry block.
        - Reserved allocations linked to a Pending Review enquiry ONLY block if hold_expires_at > now.
        - Expired holds or cancelled/completed/rejected enquiries NEVER block.
        """
        now = datetime.now(timezone.utc)

        # Active blocking condition considering enquiry status and hold expiry
        active_blocking_condition = or_(
            RentalAllocation.status == AllocationStatus.CONFIRMED,
            and_(
                RentalAllocation.status == AllocationStatus.RESERVED,
                RentalAllocation.enquiry_id.is_(None),
            ),
            and_(
                RentalAllocation.status == AllocationStatus.RESERVED,
                RentalAllocation.enquiry_id.is_not(None),
                RentalEnquiry.status == EnquiryStatus.PENDING_REVIEW,
                RentalEnquiry.hold_expires_at > now,
            ),
            and_(
                RentalAllocation.status == AllocationStatus.RESERVED,
                RentalAllocation.enquiry_id.is_not(None),
                RentalEnquiry.status == EnquiryStatus.CONFIRMED,
            ),
        )

        stmt = (
            select(RentalAllocation.unit_id)
            .outerjoin(RentalEnquiry, RentalAllocation.enquiry_id == RentalEnquiry.id)
            .where(
                active_blocking_condition,
                RentalAllocation.start_date <= end_date,
                RentalAllocation.end_date >= start_date,
            )
            .distinct()
        )
        return db.scalars(stmt).all()

    @classmethod
    def get_available_units_for_equipment(
        cls, db: Session, equipment_id: uuid.UUID, start_date: date, end_date: date
    ) -> List[EquipmentUnit]:
        """
        Find all active units for an equipment item that are NOT booked for the date range.
        """
        blocked_unit_ids = cls.get_overlapping_unit_ids(
            db, start_date=start_date, end_date=end_date
        )

        query = select(EquipmentUnit).where(
            EquipmentUnit.equipment_id == equipment_id,
            EquipmentUnit.operational_status == UnitOperationalStatus.ACTIVE,
        )
        if blocked_unit_ids:
            query = query.where(EquipmentUnit.id.not_in(blocked_unit_ids))

        query = query.order_by(EquipmentUnit.asset_code.asc())
        return db.scalars(query).all()

    @classmethod
    def check_product_availability(
        cls,
        db: Session,
        product_id: str,
        start_date: date,
        end_date: date,
        quantity: int = 1,
    ) -> ProductAvailabilityResponse:
        """Check availability for a single catalogue product."""
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End date cannot be earlier than start date",
            )
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quantity must be greater than or equal to 1",
            )

        eq = db.scalar(select(Equipment).where(Equipment.product_id == product_id))
        if not eq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )

        # Count total active physical units
        total_active_stmt = select(func.count(EquipmentUnit.id)).where(
            EquipmentUnit.equipment_id == eq.id,
            EquipmentUnit.operational_status == UnitOperationalStatus.ACTIVE,
        )
        total_active = db.scalar(total_active_stmt) or 0

        # Find available units
        avail_units = cls.get_available_units_for_equipment(
            db, equipment_id=eq.id, start_date=start_date, end_date=end_date
        )
        available_qty = len(avail_units)
        is_avail = available_qty >= quantity
        avail_asset_codes = [u.asset_code for u in avail_units]

        return ProductAvailabilityResponse(
            product_id=eq.product_id,
            product_name=eq.name,
            start_date=start_date,
            end_date=end_date,
            total_active_units=total_active,
            available_quantity=available_qty,
            requested_quantity=quantity,
            is_available=is_avail,
            available_asset_codes=avail_asset_codes,
        )

    @classmethod
    def check_kit_availability(
        cls,
        db: Session,
        kit_id: str,
        start_date: date,
        end_date: date,
        quantity: int = 1,
    ) -> KitAvailabilityResponse:
        """
        Check availability of all catalogue-linked components of a Creator Kit.
        Independent components (not linked to catalogue equipment) are reported
        as bundled without generating invented inventory checks.
        """
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End date cannot be earlier than start date",
            )
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quantity must be greater than or equal to 1",
            )

        stmt = (
            select(CreatorKit)
            .options(
                joinedload(CreatorKit.items).joinedload(CreatorKitItem.equipment)
            )
            .where(CreatorKit.kit_id == kit_id)
        )
        kit = db.scalar(stmt)
        if not kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Creator Kit '{kit_id}' not found",
            )

        components_resp: List[KitComponentAvailability] = []
        kit_is_available = True

        for item in kit.items:
            req_component_qty = item.quantity * quantity
            if item.equipment:
                # Catalogue linked component: verify physical units
                avail_units = cls.get_available_units_for_equipment(
                    db,
                    equipment_id=item.equipment.id,
                    start_date=start_date,
                    end_date=end_date,
                )
                avail_qty = len(avail_units)
                comp_avail = avail_qty >= req_component_qty
                if not comp_avail:
                    kit_is_available = False
                    reason = f"Only {avail_qty} unit(s) available, {req_component_qty} required"
                else:
                    reason = None

                components_resp.append(
                    KitComponentAvailability(
                        role=item.role,
                        name=item.name,
                        product_id=item.equipment.product_id,
                        is_catalogue_linked=True,
                        required_quantity=req_component_qty,
                        available_quantity=avail_qty,
                        is_available=comp_avail,
                        reason=reason,
                    )
                )
            else:
                # Independent component: does not generate inventory check
                components_resp.append(
                    KitComponentAvailability(
                        role=item.role,
                        name=item.name,
                        product_id=None,
                        is_catalogue_linked=False,
                        required_quantity=req_component_qty,
                        available_quantity=None,
                        is_available=True,
                        reason="Bundled independent accessory",
                    )
                )

        return KitAvailabilityResponse(
            kit_id=kit.kit_id,
            kit_title=kit.title,
            start_date=start_date,
            end_date=end_date,
            requested_quantity=quantity,
            is_available=kit_is_available,
            components=components_resp,
        )

    @classmethod
    def check_combined_availability(
        cls, db: Session, request: CombinedAvailabilityCheckRequest
    ) -> CombinedAvailabilityCheckResponse:
        """
        Check availability across multiple products and an optional Creator Kit.
        Takes into account the combined required quantity per catalogue product.
        """
        start_date = request.start_date
        end_date = request.end_date

        # Total requirements per equipment_id: UUID -> (Equipment, requested_qty)
        requirements: Dict[uuid.UUID, Tuple[Equipment, int]] = {}

        # 1. Kit components requirements
        kit_response: Optional[KitAvailabilityResponse] = None
        if request.kit_id:
            kit_response = cls.check_kit_availability(
                db, kit_id=request.kit_id, start_date=start_date, end_date=end_date
            )
            stmt = (
                select(CreatorKit)
                .options(
                    joinedload(CreatorKit.items).joinedload(CreatorKitItem.equipment)
                )
                .where(CreatorKit.kit_id == request.kit_id)
            )
            kit = db.scalar(stmt)
            for item in kit.items:
                if item.equipment:
                    eq = item.equipment
                    cur_qty = requirements.get(eq.id, (eq, 0))[1]
                    requirements[eq.id] = (eq, cur_qty + item.quantity)

        # 2. Individual product requirements
        for p_sel in request.product_selections:
            pid = p_sel.product_id.strip()
            eq = db.scalar(select(Equipment).where(Equipment.product_id == pid))
            if not eq:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{pid}' not found",
                )
            cur_qty = requirements.get(eq.id, (eq, 0))[1]
            requirements[eq.id] = (eq, cur_qty + p_sel.quantity)

        # 3. Verify total availability per equipment
        products_report: List[ProductAvailabilityReport] = []
        overall_available = True if (not kit_response or kit_response.is_available) else False

        for eq_id, (eq, total_required) in requirements.items():
            avail_units = cls.get_available_units_for_equipment(
                db, equipment_id=eq_id, start_date=start_date, end_date=end_date
            )
            avail_qty = len(avail_units)
            is_avail = avail_qty >= total_required
            if not is_avail:
                overall_available = False
                reason = f"Only {avail_qty} unit(s) available, {total_required} required"
            else:
                reason = None

            products_report.append(
                ProductAvailabilityReport(
                    product_id=eq.product_id,
                    product_name=eq.name,
                    requested_quantity=total_required,
                    available_quantity=avail_qty,
                    is_available=is_avail,
                    reason=reason,
                )
            )

        return CombinedAvailabilityCheckResponse(
            start_date=start_date,
            end_date=end_date,
            is_available=overall_available,
            products=products_report,
            kit=kit_response,
        )

    @classmethod
    def allocate_units(
        cls,
        db: Session,
        allocations_to_make: List[Tuple[str, int]],  # List of (product_id, quantity)
        start_date: date,
        end_date: date,
        status_to_set: AllocationStatus = AllocationStatus.RESERVED,
        enquiry_reference: Optional[str] = None,
        enquiry_id: Optional[uuid.UUID] = None,
        auto_commit: bool = True,
    ) -> List[RentalAllocation]:
        """
        Safely allocate physical equipment units inside a database transaction.
        Rolls back all allocations if any requested item cannot be fulfilled or if
        a PostgreSQL exclusion constraint violation occurs.
        If auto_commit is False, flushes allocations instead of committing, allowing
        outer transactions (such as enquiry submission) to commit atomically.
        """
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End date cannot be earlier than start date",
            )

        allocated_records: List[RentalAllocation] = []

        try:
            # Atomic allocation attempt
            for product_id, quantity in allocations_to_make:
                if quantity <= 0:
                    continue

                eq = db.scalar(
                    select(Equipment).where(Equipment.product_id == product_id)
                )
                if not eq:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product '{product_id}' not found",
                    )

                # Fetch available units for this product
                available_units = cls.get_available_units_for_equipment(
                    db, equipment_id=eq.id, start_date=start_date, end_date=end_date
                )

                if len(available_units) < quantity:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"Insufficient inventory for '{eq.name}'. "
                            f"Requested: {quantity}, Available: {len(available_units)}"
                        ),
                    )

                # Allocate first N available units
                for unit in available_units[:quantity]:
                    alloc = RentalAllocation(
                        unit_id=unit.id,
                        start_date=start_date,
                        end_date=end_date,
                        status=status_to_set,
                        enquiry_reference=enquiry_reference,
                        enquiry_id=enquiry_id,
                    )
                    db.add(alloc)
                    allocated_records.append(alloc)

            if auto_commit:
                db.commit()
                for record in allocated_records:
                    db.refresh(record)
            else:
                db.flush()

            return allocated_records

        except IntegrityError as exc:
            if auto_commit:
                db.rollback()
            logger.warning("Allocation constraint violation: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Concurrent booking conflict detected: one or more selected units were just reserved. Please try again.",
            )
        except Exception:
            if auto_commit:
                db.rollback()
            raise
