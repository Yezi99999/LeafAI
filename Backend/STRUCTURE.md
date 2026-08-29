# LeafAI‑Backend AI 平台后台架构设计

> 
> 业务范围：对话 Chat、图片生成、视频生成、语音 TTS/ASR；**支持同一个业务模块，多服务商、多 token、多 base_url 自定义**；技术栈：FastAPI + SQLAlchemy (异步) + Pydantic v2 + Redis + Celery (长任务)；纯后端架构，不含前端代码。

## 核心需求要点

1. 同一能力模块（例如对话 chat），可以配置多个模型服务商：OpenAI / DeepSeek / 本地 Ollama / 通义千问等，每个服务商拥有独立 `api_key`、独立 `base_url`。
2. 不同能力：对话、图片、视频、语音，各自可以挂载多个后端实例。
3. 区分：同步调用（对话、tts）、流式 SSE 调用（chat 流式）、异步长任务（图片、视频生成，耗时久）。
4. 任务状态持久化，支持轮询查询结果；支持失败重试；权限隔离；统一返回格式。
5. 适配器模式：新增模型厂商不需要修改业务逻辑，只新增适配器。

---

# 1. 整体分层架构

```
┌─────────────────────────────────────────────┐
│ API 路由层（FastAPI Router）                  │
│ chat_router / image_router / video_router / audio_router
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ Service业务层                                 │
│ AI服务调度器：根据model_id查找服务商配置，分发请求
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ Adapter适配器层【核心】                       │
│ ChatAdapter / ImageAdapter / VideoAdapter / AudioAdapter
│ 每个适配器实现统一接口，内部处理不同厂商token、url、请求体转换
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ Task任务层 Celery异步任务                     │
│ 图片/视频属于长耗时任务，丢入队列执行
└───────────────┬─────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ 存储层：PostgreSQL + Redis                   │
│ PG：服务商配置、任务记录、对话历史、用户
│ Redis：SSE会话缓存、任务状态缓存、限流
└─────────────────────────────────────────────┘
```

### 核心设计思想：适配器 + 调度器

- **Provider 服务商配置表**：保存每个服务商的 `type(chat/image/video/audio)`、`api_key`、`base_url`、启用状态、权重、超时参数。
- **Model 模型表**：逻辑模型，绑定一个 provider；对外前端只传`model_id`，后端自动读取该模型对应的 token、url，**前端不需要感知底层服务商地址密钥**。

> 
> ✅实现：同一个对话模块，可以同时存在多个 provider，不同 model_id 对应不同 token、不同 url。

---

# 2. 数据库核心表设计（关键字段）

## 2.1 ai_provider 服务商配置表（多 token、多 url 存储核心）

表格

| 字段 | 说明 |
| --- | --- |
| id | 主键 |
| name | 服务商名称：deepseek‑chat、openai‑gpt4、ollama‑local |
| category | 能力分类：`chat` / `image` / `video` / `audio` |
| api_key | 服务商 token，可以为空（本地 ollama 不需要 key） |
| base_url | 自定义请求地址，支持私有化部署，例如 `http://127.0.0.1:11434/v1` |
| timeout | 接口超时秒数 |
| extra_config | JSON 字段，厂商特殊参数：如 api_version、region、model_name 映射 |
| is_enabled | 是否启用 |
| priority | 调度权重，用于负载 |

> 
> 举例：
> 两条 category=chat 的记录：
> 
> 
> 1. deepseek：api_key=sk‑xxx，base_url=[https://api.deepseek.com/v1](https://api.deepseek.com/v1)
> 2. local‑ollama：api_key=""，base_url=[http://127.0.0.1:11434/v1](http://127.0.0.1:11434/v1)

## 2.2 ai_model 逻辑模型表

> 
> 对外暴露给前端使用，绑定 provider
> | 字段 | 说明 |
> |---|---|
> |id|model_id，前端请求传入这个 id|
> |display_name | 页面展示名字 |
> |provider_id | 外键关联 ai_provider.id|
> |category|`chat/image/video/audio`|
> |model_name | 服务商侧真实模型名称，例如 `deepseek‑v3` / `qwen‑vl`|
> |is_default | 是否该分类默认模型 |

> 
> 前端调用只传递 `model_id`，不需要传 token、url；后端查询 model 拿到 provider_id，再读取 provider 的 api_key/base_url。

## 2.3 ai_chat_session 对话会话表

存储用户对话会话，多轮对话

表格

| 字段 | 说明 |
| --- | --- |
| id | 会话 id |
| user_id | 所属用户 |
| model_id | 使用的模型 id |
| title | 会话标题 |
| create_time | 创建时间 |

## 2.4 ai_chat_message 对话消息表

单条消息，role/content，多轮历史持久化

## 2.5 ai_task 异步任务表（图片 / 视频生成）

图片、视频生成是长耗时任务，全部转为任务模式

表格

| 字段 | 说明 |
| --- | --- |
| task_id | uuid 任务 id，前端轮询用 |
| user_id | 用户 |
| category | `image_generate` / `video_generate` |
| model_id | 使用的模型 |
| status | pending / running / success / failed |
| input_params | JSON，入参：提示词、分辨率、步数等 |
| result | JSON，输出：图片 url、视频 url |
| error_msg | 失败原因 |

## 2.6 user 用户表

用户鉴权，权限控制

---

#3. 适配器层统一接口定义（伪代码）

> 
> 所有适配器强制实现统一接口，不同厂商内部实现请求转换，上层业务不需要关心底层 http 细节。

```
# 基础抽象适配器
from abc import ABC, abstractmethod

class BaseAIClient(ABC):
    def __init__(self, provider_config: dict):
        """provider_config来自ai_provider表：api_key, base_url, extra_config"""
        self.api_key = provider_config["api_key"]
        self.base_url = provider_config["base_url"]
        self.extra = provider_config["extra_config"]

# ========= Chat对话适配器 =========
class ChatClient(BaseAIClient):
    @abstractmethod
    async def chat_completion(self, messages: list, model_name: str, stream: bool = False):
        """
        stream=True 返回异步迭代器用于SSE流式输出
        stream=False 返回完整json结果
        """
        pass

# ========= 图片生成适配器 =========
class ImageClient(BaseAIClient):
    @abstractmethod
    async def generate(self, prompt: str, size: str, n: int):
        pass

# ========= 视频生成适配器 =========
class VideoClient(BaseAIClient):
    @abstractmethod
    async def generate(self, prompt: str, image_input: str = None):
        pass

# ========= 语音适配器 TTS/ASR =========
class AudioClient(BaseAIClient):
    @abstractmethod
    async def tts(self, text: str):
        pass
    @abstractmethod
    async def asr(self, audio_bytes):
        pass
```

**调度器逻辑伪代码**

```
async def get_ai_client(model_id:int):
    # 1.查询model表，拿到provider_id
    model = await db.query_model(model_id)
    # 2.查询provider配置，拿到该模型专属api_key、base_url
    provider = await db.query_provider(model.provider_id)
    # 3.根据category自动选择对应的适配器
    if model.category == "chat":
        return DeepSeekChatClient(provider)
    elif model.category == "image":
        return OpenAIImageClient(provider)
    # ...其他适配器
```

> 
> 新增一个厂商，只需要新增一个 XXClient 适配器，不需要修改路由、业务逻辑。

---

#4.API 接口设计

## 4.1 Chat 对话模块

1. `POST /api/v1/chat/completions`

- 支持普通返回、SSE 流式返回；传入`model_id`，messages[]
- 多轮对话：支持传入`session_id`读取历史；也支持直接传 messages

> 
> SSE 场景：适配器返回 async 迭代器，FastAPI 直接包装为 StreamingResponse。

##4.2 图片生成（异步任务）
`POST /api/v1/image/generate`

- 请求：`model_id`、prompt、size
- 返回：`task_id`，**不会直接返回图片**，交给 celery 后台执行
`GET /api/v1/task/{task_id}`
- 查询任务状态、图片结果 url

##4.3 视频生成（异步任务）
`POST /api/v1/video/generate`

- 支持文生视频、图生视频；返回 task_id
`GET /api/v1/task/{task_id}` 查询任务

##4.4 语音模块
`POST /api/v1/audio/tts` 文本转语音，返回音频二进制
`POST /api/v1/audio/asr` 上传音频文件，返回识别文本

##4.5 管理接口（后台）
`GET /api/v1/admin/providers` 获取所有服务商配置
`POST /api/v1/admin/providers` 添加服务商，填写独立 token、url
`GET /api/v1/admin/models` 管理逻辑模型，绑定 provider

> 
> 关键点：**密钥、base_url 全部保存在后端数据库，前端永远拿不到 token**。

---

#5. 关键技术点
##5.1 同一模块多 token 多 URL 如何实现
示例：对话 chat 模块，2 套不同配置

1. 在`ai_provider`插入两条`category=chat`记录

- provider1：DeepSeek，`api_key=sk‑aaa`，`base_url=https://api.deepseek.com/v1`
- provider2：本地 Ollama，`api_key=""`，`base_url=http://127.0.0.1:11434/v1`

2. 在`ai_model`创建两条 model，分别绑定两个 provider

- model_id=1 → deepseek 模型
- model_id=2 → ollama 模型

3. 前端请求对话接口，传不同 model_id，调度器自动加载对应 token 和 base_url，上层业务代码完全不用改动。

##5.2 同步 / 异步区分

- **对话、TTS**：同步；chat 支持流式 SSE；
- **图片、视频**：耗时很长，全部走 Celery 异步任务队列；接口提交任务，轮询 task_id 获取结果。

##5.3 Redis 用途

1. SSE 会话缓存：保存流式输出临时上下文
2. 任务状态缓存，加速 task 查询
3. 限流：每个 provider 做调用频率限制，防止 token 被滥用

##5.4 文件存储
图片、视频、语音文件：保存到对象存储 /minio；数据库只存访问 url。

##5.5 统一返回格式

```
{
    "code":0,
    "msg":"ok",
    "data":{...}
}
```

##5.6 异常处理

- 适配器层捕获第三方 API 报错；统一包装业务异常；区分：token 失效、网络超时、模型拒绝、配额耗尽。

---

#6. 目录结构建议（FastAPI 项目）

```
Backend/
├── app/
│   ├── api/                # 路由层
│   │   ├── v1
│   │   │   ├── chat.py
│   │   │   ├── image.py
│   │   │   ├── video.py
│   │   │   ├── audio.py
│   │   │   ├── task.py
│   │   │   └── admin.py
│   ├── core/               # 全局配置、异常、安全
│   ├── db/                 # orm模型、数据库会话
│   ├── schemas/            # pydantic请求响应schema
│   ├── services/           # 业务调度层
│   │   └── ai_scheduler.py # AI调度器，根据model_id拿到client
│   ├── adapters/           # 适配器【重点】
│   │   ├── base.py
│   │   ├── chat
│   │   ├── image
│   │   ├── video
│   │   └── audio
│   ├── tasks/              # celery异步任务
│   └── utils/
├── pyproject.toml
└── main.py
```

---

#7. 扩展能力

1. 负载均衡：同一个 category 多个 provider，支持权重调度；
2. 降级：服务商调用失败自动切换同类型其他 provider；
3. 用量统计：记录每个 provider 调用次数、token 消耗；
4. 租户隔离：不同用户可以配置自己的 api_key（私有化场景）；
5. 支持 OpenAI 兼容接口，很多本地模型都兼容 openai 协议，适配器可以复用。
