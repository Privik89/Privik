from fastapi import APIRouter

from .routers import ingest, click, soc, zero_trust, email_gateway


api_router = APIRouter()
api_router.include_router(ingest.router)
api_router.include_router(click.router)
api_router.include_router(soc.router)
api_router.include_router(zero_trust.router)
api_router.include_router(email_gateway.router)


