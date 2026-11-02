from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.availability import (
    CombinedAvailabilityCheckRequest,
    CombinedAvailabilityCheckResponse,
    KitAvailabilityResponse,
    ProductAvailabilityResponse,
)
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get(
    "/equipment/{product_id}",
    response_model=ProductAvailabilityResponse,
    summary="Check product date-wise availability",
    description="Check available physical inventory units for a catalogue product over a requested date range.",
)
def get_equipment_availability(
    product_id: str,
    start_date: date = Query(..., alias="startDate", description="Rental start date"),
    end_date: date = Query(..., alias="endDate", description="Rental end date"),
    quantity: int = Query(1, ge=1, description="Requested units quantity"),
    db: Session = Depends(get_db),
):
    return AvailabilityService.check_product_availability(
        db=db,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        quantity=quantity,
    )


@router.get(
    "/kits/{kit_id}",
    response_model=KitAvailabilityResponse,
    summary="Check Creator Kit component availability",
    description="Check physical inventory availability for all catalogue-linked components of a Creator Kit.",
)
def get_kit_availability(
    kit_id: str,
    start_date: date = Query(..., alias="startDate", description="Rental start date"),
    end_date: date = Query(..., alias="endDate", description="Rental end date"),
    quantity: int = Query(1, ge=1, description="Requested kit quantity"),
    db: Session = Depends(get_db),
):
    return AvailabilityService.check_kit_availability(
        db=db,
        kit_id=kit_id,
        start_date=start_date,
        end_date=end_date,
        quantity=quantity,
    )


@router.post(
    "/check",
    response_model=CombinedAvailabilityCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check combined product and kit availability",
    description="Aggregated date-wise availability check for multiple products and optional Creator Kit.",
)
def check_combined_availability(
    payload: CombinedAvailabilityCheckRequest,
    db: Session = Depends(get_db),
):
    return AvailabilityService.check_combined_availability(db=db, request=payload)
