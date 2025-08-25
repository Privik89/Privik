from fastapi import APIRouter

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("/ping")
def ping():
    return {"message": "ingest up"}


