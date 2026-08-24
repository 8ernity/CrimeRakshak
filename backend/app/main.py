"""FastAPI application entrypoint for the Auth & RBAC module.

Run locally with::

    cd backend
    uvicorn app.main:app --reload

Only Authentication & RBAC are wired here. Graph Intelligence and Financial
Crime routers are intentionally out of scope for this step; their protected
placeholders live in ``app/routers/protected.py``.
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os

from app.core.config import settings
from app.core.exceptions import AppHTTPException
from app.core.logging import get_logger
from app.financial.routers import financial as financial_router
from app.graph.routers import graph as graph_router
from app.chat.router import router as chat_router
from app.investigation_ai.router import router as investigation_router
from app.routers import admin, analytics, auth, network, predict, protected

logger = get_logger("api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Authentication & Role-Based Access Control module.",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers → consistent error envelope ────────────────────────
@app.exception_handler(AppHTTPException)
async def app_http_exception_handler(request: Request, exc: AppHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "request validation failed",
                "details": exc.errors(),
            }
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(protected.router, prefix=settings.API_V1_PREFIX)
app.include_router(graph_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(financial_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(network.router, prefix=settings.API_V1_PREFIX)
app.include_router(predict.router, prefix=settings.API_V1_PREFIX)
app.include_router(investigation_router, prefix=settings.API_V1_PREFIX)



# ── Lifecycle ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def _startup_seed() -> None:
    """Seed the database with default roles, permissions, and the superuser on startup."""
    from app.seed import seed
    try:
        logger.info("Running automatic DB seeding on startup...")
        seed()
        logger.info("Automatic DB seeding completed.")
    except Exception as e:
        logger.error(f"Failed to auto-seed database: {e}")

    try:
        from app.chat.data.case_generator import generate as generate_cases
        from app.chat.data.loader import build_database
        logger.info("Generating synthetic cases and building DuckDB dataset...")
        generate_cases()
        build_database()
        logger.info("DuckDB dataset built successfully.")
    except Exception as e:
        logger.error(f"Failed to build DuckDB dataset: {e}")


@app.on_event("shutdown")
def _shutdown_graph() -> None:
    """Close the shared Neo4j driver cleanly on application shutdown."""
    from app.graph.connection import graph_connection

    graph_connection.close()


@app.get("/health", tags=["system"], summary="Liveness probe")
def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/health/graph", tags=["system"], summary="Graph DB connectivity probe")
def health_graph():
    from app.graph.connection import graph_connection

    ok = graph_connection.verify_connectivity()
    return {"status": "ok" if ok else "unavailable", "component": "neo4j"}


@app.get("/", tags=["system"], include_in_schema=False)
def root():
    return {"service": settings.PROJECT_NAME, "docs": "/docs"}


@app.get("/app-release.apk", tags=["system"], summary="Download Mobile App")
def download_app():
    apk_path = os.path.join(os.path.dirname(__file__), "../static/app-release.apk")
    if os.path.exists(apk_path):
        return FileResponse(apk_path, media_type="application/vnd.android.package-archive", filename="CrimeRakshak.apk")
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
