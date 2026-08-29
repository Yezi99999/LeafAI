from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class TaskStatusResponse(BaseModel):
    task_id: str
    category: str
    status: str
    input_params: Optional[dict] = None
    result: Optional[dict] = None
    error_msg: Optional[str] = None
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskStatusResponse]
    total: int