from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class BaseResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: Any = None