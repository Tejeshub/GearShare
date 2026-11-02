from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.security import verify_admin_key
from app.db.dependencies import get_db
from app.models.enquiry import EnquiryStatus
from app.schemas.catalog import PaginatedResponse
from app.schemas.enquiry import (
    EnquirySubmissionPayload,
    EnquirySubmissionResult,
    RentalEnquiryDetail,
    UpdateEnquiryStatusRequest,
)
from app.schemas.rentals import RentalQuoteRequest, RentalQuoteResponse
from app.services.enquiry_service import EnquiryService
from app.services.rental_quote_service import RentalQuoteService

router = APIRouter(prefix="/rentals", tags=["Rentals"])


# -------------------------------------------------------------
# Rental Quote Endpoint
# -------------------------------------------------------------
@router.post(
    "/quote",
    response_model=RentalQuoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate rental quote",
    description="Calculate an accurate, itemized rental quote for selected equipment and optional Creator Kits with inclusive calendar-day duration.",
)
def get_rental_quote(
    payload: RentalQuoteRequest,
    db: Session = Depends(get_db),
):
    return RentalQuoteService.calculate_quote(db=db, request=payload)


# -------------------------------------------------------------
# Rental Enquiry Submission (with Idempotency-Key support)
# -------------------------------------------------------------
@router.post(
    "/enquiries",
    response_model=EnquirySubmissionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a rental enquiry",
    description="Atomically validate request, calculate quote, reserve inventory units, and create enquiry under 24h temporary hold.",
)
def submit_rental_enquiry(
    payload: EnquirySubmissionPayload,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    return EnquiryService.submit_enquiry(
        db=db, payload=payload, idempotency_key=idempotency_key
    )


# -------------------------------------------------------------
# Enquiry Retrieval & Internal Management
# -------------------------------------------------------------
@router.get(
    "/enquiries/{reference}",
    response_model=RentalEnquiryDetail,
    summary="Get customer rental enquiry by reference",
    description="Retrieve customer-facing status, dates, quote, and itemized equipment breakdown.",
)
def get_enquiry_by_reference(
    reference: str,
    db: Session = Depends(get_db),
):
    return EnquiryService.get_enquiry_by_reference(db=db, reference=reference)


@router.get(
    "/enquiries",
    response_model=PaginatedResponse[RentalEnquiryDetail],
    summary="List rental enquiries (Admin Only)",
    description="Administrative management endpoint to list enquiries with filtering and pagination. Requires authentication.",
)
def list_rental_enquiries(
    status_filter: Optional[EnquiryStatus] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[date] = Query(None, alias="startDate", description="Filter start date"),
    end_date: Optional[date] = Query(None, alias="endDate", description="Filter end date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Page size"),
    _admin: str = Depends(verify_admin_key),
    db: Session = Depends(get_db),
):
    return EnquiryService.list_enquiries(
        db=db,
        status_filter=status_filter,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )


@router.patch(
    "/enquiries/{reference}/status",
    response_model=RentalEnquiryDetail,
    summary="Update rental enquiry status (Admin Only)",
    description="Transition enquiry status according to the lifecycle state diagram (e.g. Pending Review -> Confirmed/Rejected/Cancelled). Requires administrative authentication.",
)
def update_enquiry_status(
    reference: str,
    payload: UpdateEnquiryStatusRequest,
    _admin: str = Depends(verify_admin_key),
    db: Session = Depends(get_db),
):
    return EnquiryService.update_enquiry_status(
        db=db, reference=reference, new_status=payload.status
    )
