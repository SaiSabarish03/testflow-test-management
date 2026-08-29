from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.database import check_database_connection
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.projects import router as projects_router
from app.api.test_suites import router as test_suites_router
from app.api.test_cases import router as test_cases_router
from app.api.test_runs import router as test_runs_router
from app.api.defects import router as defects_router

app = FastAPI(
    title="TestFlow API",
    description="Test Management System REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(test_suites_router)
app.include_router(test_cases_router)
app.include_router(test_runs_router)
app.include_router(defects_router)


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def health_check():
    """Application liveness — confirms the process is running."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/health/db", tags=["health"])
def database_health_check():
    """Database readiness — executes SELECT 1 against MySQL."""
    if check_database_connection():
        return {"status": "ok", "database": "connected"}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "error", "database": "unreachable"},
    )


# ---------------------------------------------------------------------------
# OpenAPI — add Bearer security scheme
# ---------------------------------------------------------------------------

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[method-assign]
