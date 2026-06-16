from fastapi import APIRouter

from app.api.routes import glossary

api_router = APIRouter(prefix="/api")
api_router.include_router(glossary.router)
