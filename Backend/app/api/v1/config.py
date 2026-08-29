import json
from pathlib import Path
from fastapi import APIRouter
from app.schemas.common import BaseResponse

router = APIRouter(prefix="/config", tags=["配置"])

_RESOLUTION_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "分辨率.json"


@router.get("/resolutions", response_model=BaseResponse)
async def get_resolutions():
    if _RESOLUTION_CONFIG_PATH.exists():
        with open(_RESOLUTION_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"aspect_ratios": []}

    return BaseResponse(data=data)