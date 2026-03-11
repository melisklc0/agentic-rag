from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    success: bool = Field(default=True)
    data: Optional[DataT] = None
    meta: Optional[dict[str, Any]] = None
    request_id: Optional[str] = None
