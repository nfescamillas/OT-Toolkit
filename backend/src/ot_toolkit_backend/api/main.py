from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .auth import hash_password
from .routers import auth, data_tools, discovery, modbus, network, preferences, reference
from .store import InMemoryStore


API_PREFIX = "/api/v1"


def error_response(status_code: int, code: str, message: str, field: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "field": field},
    )


def create_app(store: InMemoryStore | None = None) -> FastAPI:
    application = FastAPI(
        title="OT Toolkit Backend API",
        version="1.0.0",
        description="In-memory FastAPI adapter for the OT Toolkit service contract.",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
    )
    application.state.store = store or InMemoryStore()
    if application.state.store.get_user("demo") is None:
        application.state.store.add_user("demo", hash_password("demo-password"))

    application.include_router(auth.router, prefix=API_PREFIX)
    application.include_router(reference.router, prefix=API_PREFIX)
    application.include_router(discovery.router, prefix=API_PREFIX)
    application.include_router(preferences.router, prefix=API_PREFIX)
    application.include_router(data_tools.router, prefix=API_PREFIX)
    application.include_router(modbus.router, prefix=API_PREFIX)
    application.include_router(network.router, prefix=API_PREFIX)

    @application.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        location = first.get("loc", ())
        field = ".".join(str(part) for part in location if part not in {"body", "query", "path"}) or None
        return error_response(400, "invalid_input", first.get("msg", "Invalid request."), field)

    @application.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return error_response(400, "invalid_input", str(exc))

    @application.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
        message = exc.args[0] if exc.args else "The requested item was not found."
        return error_response(404, "not_found", str(message))

    @application.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code = "unauthorized" if exc.status_code == 401 else "http_error"
        response = error_response(exc.status_code, code, str(exc.detail))
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    return application


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("ot_toolkit_backend.api.main:app", host="127.0.0.1", port=8000, reload=False)

