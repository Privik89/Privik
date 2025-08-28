from fastapi import APIRouter

from .routers import ingest, click, soc


api_router = APIRouter()
api_router.include_router(ingest.router)
api_router.include_router(click.router)
api_router.include_router(soc.router)


