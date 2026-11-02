from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.catalog import router as catalog_router
from app.api.rentals import router as rentals_router
from app.api.availability import router as availability_router
from app.api.contact import router as contact_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(catalog_router)
api_router.include_router(rentals_router)
api_router.include_router(availability_router)
api_router.include_router(contact_router)

__all__ = ["api_router"]
