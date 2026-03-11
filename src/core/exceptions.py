from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class DocumentParseError(AppException):
    def __init__(self, details: Optional[Any] = None):
        super().__init__(
            code="DOC_01",
            message="Document could not be parsed",
            status_code=422,
            details=details,
        )


class DatabaseConnectionError(AppException):
    def __init__(self, details: Optional[Any] = None):
        super().__init__(
            code="DB_01",
            message="Database connection failed",
            status_code=503,
            details=details,
        )


class ResourceNotFoundError(AppException):
    def __init__(self, resource: str, details: Optional[Any] = None):
        super().__init__(
            code="RES_404",
            message=f"{resource} not found",
            status_code=404,
            details=details,
        )
