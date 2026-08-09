from fastapi import APIRouter
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.chat import router as chat_router
from app.api.v1.booking import router as booking_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(ingestion_router)
api_router.include_router(chat_router)
api_router.include_router(booking_router)
