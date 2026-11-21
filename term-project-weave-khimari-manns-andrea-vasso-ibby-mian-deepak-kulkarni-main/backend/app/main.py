from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api import stocks, screen, portfolios, questions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(
    title="WEAVE API",
    description="Financial Education & Portfolio Analysis API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router, prefix=settings.api_prefix)
app.include_router(screen.router, prefix=settings.api_prefix)
app.include_router(portfolios.router, prefix=settings.api_prefix)
app.include_router(questions.router, prefix=settings.api_prefix)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "0.1.0",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )