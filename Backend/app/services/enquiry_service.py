import hashlib
import json
import logging
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from math import ceil
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.catalog import CreatorKit, CreatorKitItem, Equipment
from app.models.enquiry import (
    EnquiryStatus,
    IdempotencyRecord,
    RentalEnquiry,
    RentalEnquiryItem,
)
from app.models.inventory import AllocationStatus, RentalAllocation
from app.schemas.catalog import PaginatedResponse
from app.schemas.enquiry import (
    EnquiryItemDetail,
    EnquirySubmissionPayload,
    EnquirySubmissionResult,
    RentalEnquiryDetail,
)
from app.schemas.rentals import RentalQuoteRequest
from app.services.availability_service import AvailabilityService
from app.services.rental_quote_service import RentalQuoteService

logger = logging.getLogger(__name__)

# Allowed status transitions
ALLOWED_TRANSITIONS: Dict[EnquiryStatus, List[EnquiryStatus]] = {
    EnquiryStatus.PENDING_REVIEW: [
        EnquiryStatus.CONFIRMED,
        EnquiryStatus.REJECTED,
        EnquiryStatus.EXPIRED,
        EnquiryStatus.CANCELLED,
    ],
    EnquiryStatus.CONFIRMED: [
        EnquiryStatus.CANCELLED,
        EnquiryStatus.COMPLETED,
    ],
    EnquiryStatus.REJECTED: [],
    EnquiryStatus.EXPIRED: [],
    EnquiryStatus.CANCELLED: [],
    EnquiryStatus.COMPLETED: [],
}


class EnquiryService:
    @staticmethod
    def generate_reference(db: Session) -> str:
        """
        Generate collision-resistant human-readable reference e.g. GS-2026-A8F2.
        Uses year + 4 uppercase hex/alphanumeric characters, verifying database uniqueness.
        """
        current_year = datetime.now(timezone.utc).year
        for _ in range(20):
            suffix = secrets.token_hex(2).upper()  # 4 characters e.g. '8F2A'
            ref = f"GS-{current_year}-{suffix}"
            exists = db.scalar(select(RentalEnquiry.id).where(RentalEnquiry.reference == ref))
            if not exists:
                return ref
        # Fallback if extremely crowded
        return f"GS-{current_year}-{secrets.token_hex(4).upper()}"

    @classmethod
    def submit_enquiry(
        cls,
        db: Session,
        payload: EnquirySubmissionPayload,
        idempotency_key: Optional[str] = None,
    ) -> EnquirySubmissionResult:
        """
        Execute atomic enquiry submission:
        1. Idempotency verification if Idempotency-Key header is provided.
        2. Recalculate quote using current DB rates.
        3. Determine equipment allocation requirements (respecting kit component deduplication).
        4. Allocate physical units within current transaction.
        5. Create RentalEnquiry with hold_expires_at = now + 24 hours.
        6. Create snapshot RentalEnquiryItem records.
        7. Associate allocations with enquiry.
        8. Store IdempotencyRecord and commit.
        """
        now = datetime.now(timezone.utc)

        # 1. Idempotency Check
        request_hash = None
        if idempotency_key:
            # Canonical JSON representation for hashing
            payload_dict = payload.model_dump(mode="json")
            payload_json = json.dumps(payload_dict, sort_keys=True)
            request_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

            existing_record = db.scalar(
                select(IdempotencyRecord).where(IdempotencyRecord.key == idempotency_key)
            )
            if existing_record:
                if existing_record.request_hash != request_hash:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Idempotency-Key was previously used with a different request payload.",
                    )
                # Return previously generated result
                return EnquirySubmissionResult.model_validate(existing_record.response_data)

        # 2. Recalculate quote using authoritative RentalQuoteService
        quote_req = RentalQuoteRequest(
            product_selections=payload.product_selections,
            kit_id=payload.kit_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        quote = RentalQuoteService.calculate_quote(db=db, request=quote_req)

        # 3. Determine required physical equipment unit allocations
        # Map: product_id -> quantity to allocate
        allocations_to_make: List[Tuple[str, int]] = []
        kit_linked_quantities: Dict[str, int] = {}
        kit_db_id = None
        kit_snapshot_components = None

        if payload.kit_id:
            stmt = (
                select(CreatorKit)
                .options(
                    joinedload(CreatorKit.items).joinedload(CreatorKitItem.equipment)
                )
                .where(CreatorKit.kit_id == payload.kit_id)
            )
            kit = db.scalar(stmt)
            if not kit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Creator Kit '{payload.kit_id}' not found",
                )
            kit_db_id = kit.id
            kit_snapshot_components = [
                {
                    "role": it.role,
                    "name": it.name,
                    "quantity": it.quantity,
                    "productId": it.equipment.product_id if it.equipment else None,
                }
                for it in kit.items
            ]

            for it in kit.items:
                if it.equipment:
                    allocations_to_make.append((it.equipment.product_id, it.quantity))
                    kit_linked_quantities[it.equipment.product_id] = (
                        kit_linked_quantities.get(it.equipment.product_id, 0) + it.quantity
                    )

        # Deduplicate additional product selections against kit inclusions
        for sel in payload.product_selections:
            pid = sel.product_id.strip()
            included_qty = kit_linked_quantities.get(pid, 0)
            chargeable_qty = sel.quantity - included_qty
            if chargeable_qty > 0:
                allocations_to_make.append((pid, chargeable_qty))

        # 4. Generate reference & prepare enquiry
        reference = cls.generate_reference(db)
        hold_expires_at = now + timedelta(hours=24)

        try:
            # 5. Create RentalEnquiry
            enquiry = RentalEnquiry(
                reference=reference,
                customer_name=payload.customer_name,
                email=payload.email,
                phone=payload.phone,
                message=payload.message,
                start_date=payload.start_date,
                end_date=payload.end_date,
                duration_days=quote.duration_days,
                subtotal=quote.subtotal,
                discount=quote.discount,
                estimated_total=quote.total,
                status=EnquiryStatus.PENDING_REVIEW,
                created_at=now,
                hold_expires_at=hold_expires_at,
            )
            db.add(enquiry)
            db.flush()  # Populates enquiry.id

            # 6. Allocate physical units atomically without auto-commit
            allocations = AvailabilityService.allocate_units(
                db=db,
                allocations_to_make=allocations_to_make,
                start_date=payload.start_date,
                end_date=payload.end_date,
                status_to_set=AllocationStatus.RESERVED,
                enquiry_reference=reference,
                enquiry_id=enquiry.id,
                auto_commit=False,
            )

            # 7. Create Enquiry Item snapshots
            # Product map for equipment_id resolution
            product_map: Dict[str, Equipment] = {}
            if payload.product_selections:
                pids = [p.product_id.strip() for p in payload.product_selections]
                for eq in db.scalars(select(Equipment).where(Equipment.product_id.in_(pids))).all():
                    product_map[eq.product_id] = eq

            for line in quote.lines:
                eq_rec = product_map.get(line.id)
                item = RentalEnquiryItem(
                    enquiry_id=enquiry.id,
                    item_type=line.type,
                    equipment_id=eq_rec.id if eq_rec else None,
                    kit_id=kit_db_id if line.type == "kit" else None,
                    name=line.name,
                    brand=line.brand,
                    daily_rate=line.daily_rate,
                    quantity=line.quantity,
                    duration_days=line.duration_days,
                    subtotal=line.subtotal,
                    bundled_components_snapshot=kit_snapshot_components if line.type == "kit" else None,
                )
                db.add(item)

            # Build result
            result = EnquirySubmissionResult(
                success=True,
                reference_id=reference,
                is_simulated=False,
                message=f"Rental enquiry {reference} received successfully. Temporary hold active for 24 hours.",
                status=EnquiryStatus.PENDING_REVIEW,
                hold_expires_at=hold_expires_at,
                quote=quote,
            )

            # 8. Record Idempotency if key supplied
            if idempotency_key and request_hash:
                idemp_rec = IdempotencyRecord(
                    key=idempotency_key,
                    request_hash=request_hash,
                    enquiry_reference=reference,
                    response_data=result.model_dump(mode="json"),
                )
                db.add(idemp_rec)

            db.commit()

            return result

        except Exception:
            db.rollback()
            raise

    @classmethod
    def get_enquiry_by_reference(cls, db: Session, reference: str) -> RentalEnquiryDetail:
        """Customer-facing enquiry lookup by reference."""
        stmt = (
            select(RentalEnquiry)
            .options(joinedload(RentalEnquiry.items))
            .where(RentalEnquiry.reference == reference)
        )
        enquiry = db.scalar(stmt)
        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rental enquiry with reference '{reference}' not found",
            )

        items_detail = [
            EnquiryItemDetail(
                id=item.id,
                item_type=item.item_type,
                name=item.name,
                brand=item.brand,
                daily_rate=item.daily_rate,
                quantity=item.quantity,
                duration_days=item.duration_days,
                subtotal=item.subtotal,
                bundled_components=item.bundled_components_snapshot,
            )
            for item in enquiry.items
        ]

        return RentalEnquiryDetail(
            id=enquiry.id,
            reference=enquiry.reference,
            customer_name=enquiry.customer_name,
            email=enquiry.email,
            phone=enquiry.phone,
            message=enquiry.message,
            start_date=enquiry.start_date,
            end_date=enquiry.end_date,
            duration_days=enquiry.duration_days,
            subtotal=enquiry.subtotal,
            discount=enquiry.discount,
            estimated_total=enquiry.estimated_total,
            status=enquiry.status,
            hold_expires_at=enquiry.hold_expires_at,
            created_at=enquiry.created_at,
            updated_at=enquiry.updated_at,
            items=items_detail,
        )

    @classmethod
    def list_enquiries(
        cls,
        db: Session,
        status_filter: Optional[EnquiryStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedResponse[RentalEnquiryDetail]:
        """Internal enquiry management listing."""
        query = select(RentalEnquiry).options(joinedload(RentalEnquiry.items))

        if status_filter:
            query = query.where(RentalEnquiry.status == status_filter)
        if start_date:
            query = query.where(RentalEnquiry.start_date >= start_date)
        if end_date:
            query = query.where(RentalEnquiry.end_date <= end_date)

        # Count total
        count_stmt = select(func.count()).select_from(query.order_by(None).subquery())
        total = db.scalar(count_stmt) or 0

        # Sort newest first
        query = query.order_by(RentalEnquiry.created_at.desc())

        offset = (page - 1) * limit
        enquiries = db.scalars(query.offset(offset).limit(limit)).unique().all()
        total_pages = ceil(total / limit) if limit > 0 else 1

        items_resp = []
        for enq in enquiries:
            items_detail = [
                EnquiryItemDetail(
                    id=item.id,
                    item_type=item.item_type,
                    name=item.name,
                    brand=item.brand,
                    daily_rate=item.daily_rate,
                    quantity=item.quantity,
                    duration_days=item.duration_days,
                    subtotal=item.subtotal,
                    bundled_components=item.bundled_components_snapshot,
                )
                for item in enq.items
            ]
            items_resp.append(
                RentalEnquiryDetail(
                    id=enq.id,
                    reference=enq.reference,
                    customer_name=enq.customer_name,
                    email=enq.email,
                    phone=enq.phone,
                    message=enq.message,
                    start_date=enq.start_date,
                    end_date=enq.end_date,
                    duration_days=enq.duration_days,
                    subtotal=enq.subtotal,
                    discount=enq.discount,
                    estimated_total=enq.estimated_total,
                    status=enq.status,
                    hold_expires_at=enq.hold_expires_at,
                    created_at=enq.created_at,
                    updated_at=enq.updated_at,
                    items=items_detail,
                )
            )

        return PaginatedResponse(
            items=items_resp,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    @classmethod
    def update_enquiry_status(
        cls, db: Session, reference: str, new_status: EnquiryStatus
    ) -> RentalEnquiryDetail:
        """
        Transition enquiry status validating allowed state diagram:
        - Confirm: changes status to Confirmed, converts allocations to CONFIRMED.
        - Reject / Cancel / Expire: releases active allocations (sets to CANCELLED).
        - Completed: marks completed, allocations become COMPLETED.
        """
        stmt = (
            select(RentalEnquiry)
            .options(
                joinedload(RentalEnquiry.items),
                joinedload(RentalEnquiry.allocations),
            )
            .where(RentalEnquiry.reference == reference)
        )
        enquiry = db.scalar(stmt)
        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rental enquiry with reference '{reference}' not found",
            )

        allowed = ALLOWED_TRANSITIONS.get(enquiry.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition from '{enquiry.status.value}' "
                    f"to '{new_status.value}'. Allowed transitions: {[s.value for s in allowed]}"
                ),
            )

        try:
            enquiry.status = new_status

            if new_status == EnquiryStatus.CONFIRMED:
                # Upgrade active allocations to CONFIRMED
                for alloc in enquiry.allocations:
                    if alloc.status == AllocationStatus.RESERVED:
                        alloc.status = AllocationStatus.CONFIRMED

            elif new_status in [
                EnquiryStatus.REJECTED,
                EnquiryStatus.CANCELLED,
                EnquiryStatus.EXPIRED,
            ]:
                # Release active allocations
                for alloc in enquiry.allocations:
                    if alloc.status in [AllocationStatus.RESERVED, AllocationStatus.CONFIRMED]:
                        alloc.status = AllocationStatus.CANCELLED

            elif new_status == EnquiryStatus.COMPLETED:
                for alloc in enquiry.allocations:
                    if alloc.status == AllocationStatus.CONFIRMED:
                        alloc.status = AllocationStatus.COMPLETED

            db.commit()
            db.refresh(enquiry)
            return cls.get_enquiry_by_reference(db, reference=reference)

        except Exception:
            db.rollback()
            raise

    @classmethod
    def cleanup_expired_enquiries(cls, db: Session) -> int:
        """
        Background maintenance job:
        Finds all Pending Review enquiries whose hold_expires_at < now (UTC).
        Transitions them to Expired and releases their allocations.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(RentalEnquiry)
            .options(joinedload(RentalEnquiry.allocations))
            .where(
                RentalEnquiry.status == EnquiryStatus.PENDING_REVIEW,
                RentalEnquiry.hold_expires_at <= now,
            )
        )
        expired_enquiries = db.scalars(stmt).unique().all()
        expired_count = len(expired_enquiries)

        for enq in expired_enquiries:
            enq.status = EnquiryStatus.EXPIRED
            for alloc in enq.allocations:
                if alloc.status == AllocationStatus.RESERVED:
                    alloc.status = AllocationStatus.CANCELLED

        db.commit()
        logger.info("Expired %d pending rental enquiries", expired_count)
        return expired_count
