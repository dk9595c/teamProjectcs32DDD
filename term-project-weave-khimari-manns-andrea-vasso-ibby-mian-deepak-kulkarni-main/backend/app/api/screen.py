"""Stock screening router."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["screen"])


@router.post("/screen")
async def screen_stocks():
    """Screen and filter stocks."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented"}
    )
