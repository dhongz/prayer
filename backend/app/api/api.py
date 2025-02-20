from fastapi import APIRouter
from .routes import auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# # api_router.include_router(tag.router, prefix="/tag", tags=["tag"])
# api_router.include_router(marketing_events.router, prefix="/marketing-events", tags=["marketing events"])
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(admin.router, prefix="/administration", tags=["administration"])
# api_router.include_router(crm.router, prefix="/crm", tags=["crm"])
# api_router.include_router(landing_page.router, prefix="/landing-page", tags=["landing page"])