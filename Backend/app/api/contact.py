import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.contact import ContactMessage
from app.schemas.contact import ContactMessageCreate, ContactMessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["Contact"])


@router.post("", response_model=ContactMessageResponse, status_code=status.HTTP_201_CREATED)
def submit_contact_message(
    payload: ContactMessageCreate,
    db: Session = Depends(get_db),
) -> ContactMessageResponse:
    """Save general contact / enquiry message from homepage."""
    contact = ContactMessage(
        name=payload.name,
        email=payload.email,
        message=payload.message,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    logger.info("Saved contact message from %s (%s)", contact.name, contact.email)
    return contact
