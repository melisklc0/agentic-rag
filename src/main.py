import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

from src.core.exceptions import AppException
from src.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    print("Application is starting...")
    yield
    # shutdown
    print("Application is shutting down...")


app = FastAPI(
    title="Enterprise Document Processing API",
    description="""
    Kurumsal seviyede doküman işleme ve veri servisleri sunan API.

    Özellikler:
    - Asenkron endpoint desteği
    - Global exception handling
    - Standart JSON hata formatı
    - OpenAPI dokümantasyonu
    - Request tracing
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Health", "description": "Servis sağlık kontrolü endpointleri"},
        {"name": "Documents", "description": "Doküman işleme işlemleri"},
    ],
    lifespan=lifespan,
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


from src.api.routers.documents import router as documents_router

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(documents_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
