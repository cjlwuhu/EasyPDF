from fastapi import APIRouter

from app.api.routes import assistant, corrections, documents, glossary, settings, translations

api_router = APIRouter(prefix="/api")
api_router.include_router(assistant.router)
api_router.include_router(corrections.router)
api_router.include_router(documents.router)
api_router.include_router(glossary.router)
api_router.include_router(settings.router)
api_router.include_router(translations.router)
