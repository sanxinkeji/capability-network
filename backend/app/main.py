from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.auth.exceptions import register_auth_exception_handlers
from app.core.config import DEFAULT_JWT_SECRET_KEY, settings
from app.core.database import get_db
from app.core.health import run_readiness_checks
from app.core.maintenance import MaintenanceModeMiddleware
from app.core.redis_client import close_redis


def init_sentry() -> None:
    if not settings.SENTRY_DSN:
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        release=settings.APP_VERSION,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    )


def validate_production_secrets() -> None:
    if settings.DEBUG:
        return
    if settings.JWT_SECRET_KEY == DEFAULT_JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY must not use the default value when DEBUG=false; "
            "set a strong random secret in .env"
        )


init_sentry()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_production_secrets()
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(MaintenanceModeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_auth_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    payload = await run_readiness_checks(db)
    status_code = 200 if payload["status"] == "ok" else 503
    return JSONResponse(status_code=status_code, content=payload)
