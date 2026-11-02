from decimal import Decimal
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import CreatorKit, CreatorKitItem, Equipment
from app.schemas.rentals import (
    BundledItemInfo,
    ItemizedQuoteLine,
    RentalQuoteRequest,
    RentalQuoteResponse,
)


def format_inr(amount: Decimal) -> str:
    """
    Format a Decimal currency amount into Indian Rupee (INR) format (e.g. ₹4,999 or ₹1,23,456).
    Uses traditional Indian number grouping: last 3 digits, then groups of 2.
    """
    # Round to nearest integer (as frontend formatINR uses maximumFractionDigits: 0)
    integer_part = int(round(amount))
    s = str(abs(integer_part))

    if len(s) <= 3:
        formatted_digits = s
    else:
        last_three = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_digits = ",".join(groups) + "," + last_three

    sign = "-" if integer_part < 0 else ""
    return f"₹{sign}{formatted_digits}"


class RentalQuoteService:
    @classmethod
    def calculate_quote(
        cls, db: Session, request: RentalQuoteRequest
    ) -> RentalQuoteResponse:
        # 1. Rental duration calculation (calendar day arithmetic, inclusive)
        start_date = request.start_date
        end_date = request.end_date

        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End date cannot be earlier than start date",
            )

        # Start Mon, End Mon = 1 day; Start Mon, End Tue = 2 days
        duration_days = (end_date - start_date).days + 1

        lines: List[ItemizedQuoteLine] = []
        # Mapping of equipment.product_id -> included quantity inside the kit
        kit_included_product_quantities: Dict[str, int] = {}

        # 2. Creator Kit processing
        if request.kit_id:
            stmt = (
                select(CreatorKit)
                .options(
                    joinedload(CreatorKit.items).joinedload(CreatorKitItem.equipment)
                )
                .where(CreatorKit.kit_id == request.kit_id)
            )
            kit = db.scalar(stmt)
            if not kit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Creator Kit '{request.kit_id}' not found",
                )
            if not kit.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Creator Kit '{request.kit_id}' is inactive and cannot be rented",
                )

            # Record included equipment components
            bundled_items_info: List[BundledItemInfo] = []
            for item in kit.items:
                product_id_linked = item.equipment.product_id if item.equipment else None
                bundled_items_info.append(
                    BundledItemInfo(
                        role=item.role,
                        name=item.name,
                        quantity=item.quantity,
                        product_id=product_id_linked,
                    )
                )
                if product_id_linked:
                    kit_included_product_quantities[product_id_linked] = (
                        kit_included_product_quantities.get(product_id_linked, 0)
                        + item.quantity
                    )

            kit_daily_rate = Decimal(str(kit.price))
            kit_subtotal = kit_daily_rate * Decimal(1) * Decimal(duration_days)

            lines.append(
                ItemizedQuoteLine(
                    id=kit.kit_id,
                    type="kit",
                    name=kit.title,
                    brand=None,
                    daily_rate=kit_daily_rate,
                    quantity=1,
                    duration_days=duration_days,
                    subtotal=kit_subtotal,
                    bundled_items=bundled_items_info,
                )
            )

        # 3. Individual Product Selections processing
        for selection in request.product_selections:
            pid = selection.product_id.strip()
            requested_qty = selection.quantity

            # Fetch product from DB
            stmt = select(Equipment).where(Equipment.product_id == pid)
            equipment = db.scalar(stmt)

            if not equipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{pid}' not found",
                )
            if not equipment.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{pid}' is inactive and cannot be rented",
                )
            if not equipment.is_rentable:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{pid}' is not available for rental",
                )

            # Check kit included quantity subtraction
            included_qty = kit_included_product_quantities.get(pid, 0)
            chargeable_qty = requested_qty - included_qty

            # If user requested more than what is bundled in the kit, charge for extra units
            if chargeable_qty > 0:
                prod_daily_rate = Decimal(str(equipment.price))
                line_subtotal = (
                    prod_daily_rate * Decimal(chargeable_qty) * Decimal(duration_days)
                )

                lines.append(
                    ItemizedQuoteLine(
                        id=equipment.product_id,
                        type="product",
                        name=equipment.name,
                        brand=equipment.brand,
                        daily_rate=prod_daily_rate,
                        quantity=chargeable_qty,
                        duration_days=duration_days,
                        subtotal=line_subtotal,
                    )
                )

        # 4. Total and subtotal calculations
        subtotal = sum((line.subtotal for line in lines), Decimal("0.00"))
        discount = Decimal("0.00")
        total = max(Decimal("0.00"), subtotal - discount)
        formatted_total = format_inr(total)

        return RentalQuoteResponse(
            lines=lines,
            duration_days=duration_days,
            subtotal=subtotal,
            discount=discount,
            total=total,
            is_provisional=True,
            formatted_total=formatted_total,
        )
