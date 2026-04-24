from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import api_router
from app.services.investment_service import sync_plans_from_json
from app.services.roi_scheduler import start_scheduler
from app.database import AsyncSessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: sync plans json to DB
    async with AsyncSessionLocal() as session:
        await sync_plans_from_json(session)
    
    # Startup: start scheduler
    start_scheduler()
    
    yield
    # Shutdown resources here

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Completed backend API for BlueWave Fixed ROI platform.",
        lifespan=lifespan
    )

    # Wide CORS for development — tighten in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler ensures CORS headers are present even on 500s
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(exc)},
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Credentials": "true",
            }
        )
    
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "success": True, 
            "message": f"Welcome to {settings.APP_NAME} API. Access /docs for documentation"
        }

    return app

app = create_app()
