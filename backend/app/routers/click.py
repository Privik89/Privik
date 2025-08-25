from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, AnyHttpUrl


class ClickRequest(BaseModel):
    original_url: AnyHttpUrl
    user_id: str
    message_id: str


router = APIRouter(prefix="/click", tags=["click"])


@router.post("/redirect")
def redirect_click(payload: ClickRequest):
    # Placeholder for click isolation logic
    # TODO: enqueue for analysis, rewrite to proxy, and return preview URL
    if not payload.original_url:
        raise HTTPException(status_code=400, detail="original_url required")

    return {
        "proxy_url": f"https://proxy.example/visit?u={payload.original_url}",
        "queued": True,
    }


