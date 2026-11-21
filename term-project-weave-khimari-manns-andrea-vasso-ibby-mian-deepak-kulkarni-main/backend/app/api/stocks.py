"""Stock data router."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["stocks"])


@router.get("/stocks")
async def list_stocks():
    """List available stocks."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented"}
    )
