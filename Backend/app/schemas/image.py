import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List

_RESOLUTION_PATH = Path(__file__).parent.parent.parent / "分辨率.json"

def _load_resolution_config() -> dict:
    if _RESOLUTION_PATH.exists():
        with open(_RESOLUTION_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"aspect_ratios": []}

MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400


class ImageGenerateRequest(BaseModel):
    model_id: int = Field(..., description="模型ID")
    prompt: str = Field(..., min_length=1, max_length=10000, description="图片生成提示词")
    resolution: Optional[str] = Field("1K", description="分辨率: 1K / 2K / 4K")
    aspect_ratio: Optional[str] = Field("1:1", description="宽高比: 1:1 / 3:2 / 2:3 / 16:9 / 9:16 等")
    quality: Optional[str] = Field("medium", description="思考深度: low / medium / high")
    image: Optional[List[str]] = Field(None, description="参考图URL列表")
    callback_url: Optional[str] = Field(None, description="异步回调地址")

    @model_validator(mode="after")
    def compute_size(self) -> "ImageGenerateRequest":
        resolution = self.resolution or "1K"
        ratio = self.aspect_ratio or "1:1"

        config = _load_resolution_config()
        for ar in config.get("aspect_ratios", []):
            if ar["ratio"] == ratio:
                res = ar["resolutions"].get(resolution)
                if res:
                    self._size = res["aligned"]
                    return self
                break

        self._size = "1024x1024"
        return self

    def get_size(self) -> str:
        return getattr(self, "_size", "1024x1024")

    def validate_size(self) -> None:
        size_str = self.get_size()
        if "x" not in size_str:
            return
        parts = size_str.split("x")
        try:
            w, h = int(parts[0]), int(parts[1])
        except ValueError:
            return
        pixels = w * h
        if pixels < MIN_PIXELS:
            raise ValueError(f"像素数({pixels})低于最小限制({MIN_PIXELS})")
        if pixels > MAX_PIXELS:
            raise ValueError(f"像素数({pixels})超过最大限制({MAX_PIXELS})")
        if w % 16 != 0 or h % 16 != 0:
            raise ValueError(f"宽高必须能被16整除, 当前: {w}x{h}")


class ImageGenerateResponse(BaseModel):
    task_id: str
    status: str = "pending"
    message: str = "任务已提交，请轮询查询结果"