from fastapi import APIRouter

from app.api.routes import documents, glossary

api_router = APIRouter(prefix="/api")
api_router.include_router(documents.router)
api_router.include_router(glossary.router)
