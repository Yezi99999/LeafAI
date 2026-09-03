# LeafAI

面向企业的 AI 集成平台。提供图片生成、对话等服务，内置管理后台（模型管理、功能开关、积分费率、用户/通知/操作审计、调用记录、报表）。

- **后端**：FastAPI + SQLAlchemy (async) + PostgreSQL，见 [`Backend/`](Backend/)
- **前端**：Vue 3 + Vite + TypeScript，见 [`Frontend/`](Frontend/)
- **接口文档**：工作台「API 服务」页面 / [`docs/api-integration.md`](docs/api-integration.md)

---

## 一、环境要求

| 组件 | 版本建议 |
| ---- | -------- |
| Python | ≥ 3.11 |
| Node.js | ≥ 18 |
| PostgreSQL | ≥ 13（需启用 `uuid-ossp` / `pgcrypto`，用于 token 默认值） |
| uv（可选）| 包管理器 |

## 二、目录结构

```
LeafAI/
├── Backend/          # FastAPI 后端
│   ├── app/          # 业务代码
│   ├── alembic/      # 数据库迁移
│   ├── init_db.py    # 数据库初始化 + 管理员设置
│   └── main.py       # 后端入口
├── Frontend/         # Vue 3 前端
└── docs/             # 设计/接口文档
```

## 三、部署步骤

### 1. 准备环境变量

复制 [`Backend/.env.example`](Backend/.env.example) 为 `Backend/.env` 并填入密钥：

```bash
# Backend/.env 至少需要：
DATABASE_URL=postgresql+asyncpg://postgres:你的密码@localhost:5432/leafai
IMAGE_API_KEY=你的图片服务密钥        # 图片服务，OpenAI 兼容参数即可
IMAGE_BASE_URL=                      # 图片服务地址，OpenAI 兼容（可选，留空用内置默认）
DEEPSEEK_API_KEY=你的对话服务密钥      # 对话服务（如 deepseek）
JWT_SECRET=请设置为随机的长字符串      # 生产必填，命令：python -c "import secrets; print(secrets.token_urlsafe(48))"
ADMIN_USERNAME=admin                  # 可选，管理员用户名
ADMIN_PASSWORD=请设置强密码            # 可选，管理员密码
```

> 图片服务采用通用的 OpenAI 兼容参数（`/images/generations`），任何具备相同参数的图片服务均可通过 `IMAGE_API_KEY` / `IMAGE_BASE_URL` 使用。

### 2. 初始化数据库并设置管理员

在 `Backend/` 目录下执行（首次部署）：

```bash
python init_db.py --admin-username "$ADMIN_USERNAME" --admin-password "$ADMIN_PASSWORD"
```

脚本会一次性完成：

1. 创建数据库（若不存在）；
2. 创建全部数据表；
3. 写入种子数据（服务商、默认模型、核心功能开关）；
4. **创建 / 更新管理员账号**（已存在则默认保留原密码）。

管理员设置的几种方式：

```bash
# 方式一：命令行参数（推荐，优先级最高）
python init_db.py --admin-username admin --admin-password 'S3cure-P@ss'

# 方式二：环境变量
ADMIN_USERNAME=admin ADMIN_PASSWORD='S3cure-P@ss' python init_db.py

# 方式三：重置已存在管理员的密码
python init_db.py --admin-username admin --admin-password '新密码' --reset-admin
```

> ⚠️ 生产环境请务必通过 `--admin-username/--admin-password` 或环境变量指定强密码；`admin/admin123` 仅为本地兜底，不建议用于生产。

### 3. 数据库迁移

后续业务模型变更通过 Alembic 迁移（`Backend/alembic/`）。升级到最新结构：

```bash
cd Backend
python -m alembic upgrade head
```

### 4. 启动后端

```bash
cd Backend
.venv\Scripts\activate          # Windows；Linux/macOS: source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

后端启动时若表缺失会自动 `create_all`，并预置核心功能开关。健康检查：`GET http://localhost:8000/health`。

开发模式（热重载）：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 启动前端

```bash
cd Frontend
npm install
npm run dev        # 开发模式
npm run build      # 生产构建
```

`VITE_API_BASE_URL` 后端地址约定：

- **开发**（`.env.development` 留空）：代码兜底直连 `http://localhost:8000`，无需配置；
- **生产**（`.env.production`）：`VITE_API_BASE_URL=/api`，走反向代理。

生产部署前端构建产物（`Frontend/dist`）到任意静态服务器（Nginx/Caddy 等），并把 `/api`（含 SSE）反向代理到后端。

## 四、默认账号与首登

初始化后会创建管理员：

- 用户名：`ADMIN_USERNAME`（未指定时为 `admin`）
- 密码：`ADMIN_PASSWORD`（未指定时为 `admin123`）

使用管理员登录前端，进入「管理后台」可进行模型管理、功能开关、积分费率、充值管理、通知群发、调用记录、操作审计、报表等操作。**首次登录后请立即修改管理员密码。**

## 五、常见问题

| 问题 | 处理 |
| ---- | ---- |
| 数据库连接失败，提示先执行 init_db.py | 确认 `.env` 中 `DATABASE_URL` 正确且 PostgreSQL 已启动，执行 `python init_db.py` |
| 通知等依赖随机 UUID 的字段报错 | 数据库需启用 `pgcrypto` 或 `uuid-ossp`：`CREATE EXTENSION IF NOT EXISTS pgcrypto;` |
| 前端登录后管理入口不可见 | 确认该账号为 `is_superuser=true` 的管理员（用 `init_db.py --reset-admin` 可强制重置） |
| SSE / 长连接超时 | 反向代理需放开 Keep-Alive 与读取超时（建议设置 `proxy_read_timeout 300s`） |

## 六、接口约定

- 所有接口（含错误响应）统一返回信封：`{ "code", "msg", "data" }`。
- 认证：`Authorization: Bearer <token>`。
- 详细见 [`docs/api-integration.md`](docs/api-integration.md)。

---

### 目录

- 业务文档：`docs/`
  - [`api-integration.md`](docs/api-integration.md) — API 接入文档（另见 HTML 版 `docs/api-integration.html`）
  - `admin-platform-design.md` — 管理后台设计
- 后端结构：`Backend/STRUCTURE.md`