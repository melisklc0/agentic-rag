import uuid
import logging

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.exceptions import AppException

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


async def app_exception_handler(request: Request, exc: AppException):
    request_id = get_request_id(request)

    logger.warning(
        "Application exception occurred",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.code,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": request_id,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = get_request_id(request)

    logger.warning(
        "Validation exception occurred",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "REQ_422",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
            "request_id": request_id,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": None,
            },
            "request_id": request_id,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = get_request_id(request)

    logger.exception(
        "Unhandled exception occurred",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "SRV_500",
                "message": "An unexpected server error occurred",
                "details": None,
            },
            "request_id": request_id,
        },
    )
