from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class BaseResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: Any = None


class PaginatedResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20