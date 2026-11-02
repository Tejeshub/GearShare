import logging
from app.db.session import SessionLocal
from app.services.enquiry_service import EnquiryService

logger = logging.getLogger("expire_enquiries")


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Running expired rental enquiries cleanup...")
    with SessionLocal() as db:
        count = EnquiryService.cleanup_expired_enquiries(db)
        logger.info("Successfully cleaned up %d expired enquiries.", count)


if __name__ == "__main__":
    main()
