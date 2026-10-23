from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    entity_id: str | None = None


class ApiError(BaseModel):
    errors: list[ErrorDetail]


class ApiResponse(BaseModel, Generic[T]):
    data: T
    warnings: list[str] = []
