import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send
from app.config import settings
from app.persistence.database import init_db
from app.api.routes import health, workforce, scenarios, schedules, datasets, manufacturing
from app.optimization.base import SolverUnavailableError
from app.services.scenario_service import ScenarioNotFoundError, ValidationFailedError
from app.services.schedule_service import RunNotFoundError, ExportNotPermittedError


class NormalizePathMiddleware:
    """Collapses consecutive duplicate slashes in the URL path (e.g. //api/schedules -> /api/schedules)."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            if "//" in path:
                scope["path"] = re.sub(r"/+", "/", path)
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Ordivanta API", version="0.1.0", lifespan=lifespan)

# 1. Path normalization middleware
app.add_middleware(NormalizePathMiddleware)

# 2. CORS middleware with Vercel and production domain allowance
cors_origins = (
    settings.allowed_origins
    if isinstance(settings.allowed_origins, list)
    else [settings.allowed_origins]
)

if "*" in cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    cors_kwargs = {
        "allow_origins": cors_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if settings.allowed_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.allowed_origin_regex
    app.add_middleware(CORSMiddleware, **cors_kwargs)


@app.exception_handler(SolverUnavailableError)
async def solver_unavailable_handler(request: Request, exc: SolverUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"errors": [{"code": "SOLVER_UNAVAILABLE", "message": str(exc)}]},
    )


@app.exception_handler(ScenarioNotFoundError)
async def scenario_not_found_handler(request: Request, exc: ScenarioNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"errors": [{"code": "SCENARIO_NOT_FOUND", "message": str(exc)}]},
    )


@app.exception_handler(RunNotFoundError)
async def run_not_found_handler(request: Request, exc: RunNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"errors": [{"code": "RUN_NOT_FOUND", "message": str(exc)}]},
    )


@app.exception_handler(ExportNotPermittedError)
async def export_not_permitted_handler(
    request: Request, exc: ExportNotPermittedError
):
    return JSONResponse(
        status_code=409,
        content={"errors": [{"code": "EXPORT_NOT_PERMITTED", "message": str(exc)}]},
    )


@app.exception_handler(ValidationFailedError)
async def validation_failed_handler(request: Request, exc: ValidationFailedError):
    errors = [
        {
            "code": e.code,
            "message": e.message,
            "field": e.field,
            "entity_id": e.entity_id,
        }
        for e in exc.errors
    ] or [{"code": "VALIDATION_FAILED", "message": str(exc)}]
    return JSONResponse(status_code=422, content={"errors": errors})


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
):
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []))
        errors.append(
            {
                "code": "INVALID_REQUEST_BODY",
                "message": err.get("msg", "Invalid field"),
                "field": field,
            }
        )
    return JSONResponse(status_code=422, content={"errors": errors})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "errors" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"errors": [{"code": "HTTP_ERROR", "message": str(exc.detail)}]},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "errors": [
                {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                }
            ]
        },
    )


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(workforce.router, prefix="/api", tags=["workforce"])
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(schedules.router, prefix="/api", tags=["schedules"])
app.include_router(datasets.router, prefix="/api", tags=["datasets"])
app.include_router(manufacturing.router, prefix="/api", tags=["manufacturing"])
