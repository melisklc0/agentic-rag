from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., examples=["DB_01"])
    message: str = Field(..., examples=["Database connection failed"])
    details: Optional[Any] = Field(default=None)


class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: ErrorDetail
    request_id: Optional[str] = None
