from fastapi import APIRouter

from app.api.routes import documents, glossary, translations

api_router = APIRouter(prefix="/api")
api_router.include_router(documents.router)
api_router.include_router(glossary.router)
api_router.include_router(translations.router)
