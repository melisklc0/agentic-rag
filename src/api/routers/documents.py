from fastapi import APIRouter
from pydantic import BaseModel

from src.core.exceptions import DocumentParseError, DatabaseConnectionError
from src.schemas.response import SuccessResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentParseRequest(BaseModel):
    filename: str
    content: str


@router.post("/parse", response_model=SuccessResponse)
async def parse_document(payload: DocumentParseRequest):
    if payload.filename.endswith(".broken"):
        raise DocumentParseError(details={"filename": payload.filename})

    if payload.filename == "db_fail.pdf":
        raise DatabaseConnectionError(details={"service": "postgres"})
    
    if payload.filename == "crash.pdf":
        # Simulate unhandled exception
        raise ValueError("Simulated crash")

    return SuccessResponse(
        data={
            "filename": payload.filename,
            "status": "parsed",
        }
    )
