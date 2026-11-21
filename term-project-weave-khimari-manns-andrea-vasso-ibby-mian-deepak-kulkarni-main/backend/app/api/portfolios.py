"""Portfolio simulation router."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["portfolios"])


@router.post("/portfolios/simulate")
async def simulate_portfolio():
    """Run portfolio backtest simulation."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented"}
    )
