"""Financial education questions router."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["questions"])


@router.get("/questions")
async def get_questions():
    """Get practice questions."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented"}
    )


@router.post("/questions/grade")
async def grade_answer():
    """Grade a student's answer."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented"}
    )
