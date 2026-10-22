from fastapi import APIRouter
from app.api.v1.routes import documents

api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Add other routers here as they are implemented
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
# api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])

__all__ = ["api_router"]