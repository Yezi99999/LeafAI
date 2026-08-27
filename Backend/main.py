from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tomllib, uvicorn
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_project_version() -> str:
    """读取 pyproject.toml 中的 version 字段"""
    # 基于当前文件路径，定位到项目根目录的 pyproject.toml
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except (FileNotFoundError, KeyError):
        return "unknown"

# 全局缓存版本号
PROJECT_VERSION = get_project_version()
PROJECT_NAME = "LeafAI"
@app.get("/")
def read_root():
    return {"ProjectName": PROJECT_NAME}

@app.get("/version")
def get_version():
    return {"version": PROJECT_VERSION}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开启热重载
    )