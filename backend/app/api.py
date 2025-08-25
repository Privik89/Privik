from fastapi import APIRouter

from .routers import ingest, click


api_router = APIRouter()
api_router.include_router(ingest.router)
api_router.include_router(click.router)


