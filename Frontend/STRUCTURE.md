# LeafAI Frontend 目录结构与业务说明

## 项目结构

```
Frontend/
├── public/                         # 静态资源（不经过构建处理，直接拷贝到 dist）
│   └── favicon.svg                 # 网站图标
├── src/                            # 源代码
│   ├── api/                        # 接口层：按业务模块拆分
│   │   ├── model.ts                # 模型管理接口
│   │   ├── training.ts             # 训练任务接口
│   │   ├── inference.ts            # 推理服务接口
│   │   ├── dataset.ts              # 数据集管理接口
│   │   └── system.ts               # 系统管理接口
│   ├── assets/                     # 静态资源：图片、全局样式、图标
│   │   ├── hero.png                # 首页主图
│   │   ├── vue.svg                 # Vue 图标
│   │   └── vite.svg                # Vite 图标
│   ├── components/                 # 公共业务组件
│   │   ├── HomePage.vue            # 示例首页（LeafAI 对话示例）
│   │   ├── ai-chat/                # AI 对话组件（流式输出、Markdown渲染）
│   │   ├── file-upload/            # 大文件分片上传组件
│   │   ├── log-stream/             # 实时日志流组件
│   │   ├── metric-chart/           # 指标监控图表组件
│   │   └── common/                 # 通用业务组件（表单、表格等）
│   ├── hooks/                      # 业务组合式 API
│   │   ├── use-sse.ts              # SSE 流式请求 Hook
│   │   ├── use-training.ts         # 训练任务通用逻辑
│   │   ├── use-model.ts            # 模型操作封装
│   │   └── use-upload.ts           # 文件上传 Hook
│   ├── layouts/                    # 后台布局：侧边栏、顶栏、标签页
│   ├── router/                     # 路由配置：静态路由 + 动态权限路由
│   │   └── routes/modules/         # 按业务模块拆分路由
│   ├── stores/                     # Pinia 状态管理
│   │   ├── user.ts                 # 用户与权限
│   │   ├── app.ts                  # 全局配置与主题
│   │   ├── model.ts                # 模型缓存
│   │   ├── training.ts             # 训练任务状态
│   │   └── chat.ts                 # 对话会话状态
│   ├── utils/                      # 工具函数：请求、格式化、校验、存储
│   ├── views/                      # 业务页面
│   │   ├── dashboard/              # 工作台/总览
│   │   ├── model/                  # 模型广场
│   │   ├── training/               # 训练管理
│   │   ├── inference/              # 推理服务
│   │   ├── dataset/                # 数据集管理
│   │   ├── monitor/                # 监控中心
│   │   └── system/                 # 系统管理
│   ├── App.vue                     # 根组件
│   ├── main.ts                     # 应用入口
│   ├── style.css                   # 全局样式
│   └── settings.ts                 # 项目全局配置
├── index.html                      # HTML 入口文件
├── package.json                    # 项目依赖与脚本
├── package-lock.json               # 依赖版本锁定
├── vite.config.ts                  # Vite 构建配置
├── tsconfig.json                   # TypeScript 总配置
├── tsconfig.app.json               # 应用代码 TS 配置
├── tsconfig.node.json              # Node 端 TS 配置（Vite 配置等）
├── .gitignore                      # Git 忽略规则
├── STRUCTURE.md                    # 本文件：项目结构说明
└── README.md                       # 项目自述文件
```

> **图例**：已存在的文件/目录标为粗体，其余为规划中的目录结构。

## 配置文件说明

### `vite.config.ts`
Vite 构建工具配置，当前使用 `@vitejs/plugin-vue` 插件处理 `.vue` 单文件组件。

### `tsconfig.json`
TypeScript 项目引用根配置，通过 `references` 分别指向 `tsconfig.app.json`（应用代码）和 `tsconfig.node.json`（构建工具代码）。

### `tsconfig.app.json`
应用代码 TS 编译配置：
- 继承 `@vue/tsconfig/tsconfig.dom.json`（Vue 官方 DOM 环境配置）
- 启用 `noUnusedLocals` / `noUnusedParameters` 严格检查
- 包含 `src/**/*.ts`、`src/**/*.tsx`、`src/**/*.vue`

### `tsconfig.node.json`
Node 端（Vite 配置等）TS 编译配置：
- 目标 `ES2023`，模块系统 `nodenext`
- 仅包含 `vite.config.ts`

### `package.json`
项目元信息与脚本：
| 脚本 | 命令 | 说明 |
|------|------|------|
| `dev` | `vite` | 启动开发服务器 |
| `build` | `vue-tsc -b && vite build` | 类型检查后构建生产包 |
| `preview` | `vite preview` | 预览生产构建结果 |

### `.gitignore`
忽略 `node_modules`、`dist`、日志文件、IDE 配置等。

### `index.html`
应用 HTML 入口，挂载点 `<div id="app">`，通过 `<script type="module" src="/src/main.ts">` 加载应用。

---

## 业务模块说明

### 1. 接口层 (`api/`)
按业务模块拆分 API 请求，统一管理接口调用与类型定义。

| 模块 | 文件 | 职责 |
|------|------|------|
| 模型管理 | `model.ts` | 模型创建、查询、版本管理、格式转换 |
| 训练任务 | `training.ts` | 训练任务创建、启停、日志获取、指标查询 |
| 推理服务 | `inference.ts` | 推理服务部署、扩缩容、流量管理 |
| 数据集管理 | `dataset.ts` | 数据集上传、标注、预处理、版本控制 |
| 系统管理 | `system.ts` | 用户管理、权限配置、资源配额、审计日志 |

### 2. 公共业务组件 (`components/`)
跨页面复用的业务组件，每个目录内含独立组件。

| 组件 | 目录 | 功能 |
|------|------|------|
| 示例首页 | `HomePage.vue` | LeafAI 对话示例页面，展示 Vue 3 Composition API 基础用法 |
| AI 对话 | `ai-chat/` | 支持流式输出（SSE）、Markdown 渲染、多轮对话 |
| 文件上传 | `file-upload/` | 大文件分片上传、断点续传、进度展示 |
| 日志流 | `log-stream/` | 实时日志流展示（WebSocket）、自动滚动、搜索过滤 |
| 指标图表 | `metric-chart/` | 训练/推理指标监控图表（ECharts） |
| 通用组件 | `common/` | 表单、表格、弹窗、加载等通用业务封装 |

### 3. 组合式 API (`hooks/`)
封装可复用的业务逻辑，遵循 Vue 3 Composition API 规范。

| Hook | 文件 | 功能 |
|------|------|------|
| SSE 流式请求 | `use-sse.ts` | 封装 EventSource/SSE 连接、重连、消息解析 |
| 训练任务 | `use-training.ts` | 训练任务生命周期管理、状态轮询 |
| 模型操作 | `use-model.ts` | 模型选择、版本切换、缓存策略 |
| 文件上传 | `use-upload.ts` | 分片上传逻辑、进度追踪、取消操作 |

### 4. 布局 (`layouts/`)
后台管理系统的布局框架，包含侧边栏导航、顶部操作栏、多标签页切换。

### 5. 路由 (`router/`)
- 静态路由：登录、404 等公共页面
- 动态路由：根据用户权限动态注册，按模块拆分在 `routes/modules/` 目录下

### 6. 状态管理 (`stores/`)
基于 Pinia 的全局状态管理，按业务领域拆分 Store。

| Store | 文件 | 职责 |
|-------|------|------|
| 用户与权限 | `user.ts` | 用户信息、Token、角色权限 |
| 全局配置 | `app.ts` | 主题、语言、侧边栏状态、布局设置 |
| 模型缓存 | `model.ts` | 模型列表缓存、当前选中模型 |
| 训练任务 | `training.ts` | 训练任务列表、实时状态 |
| 对话会话 | `chat.ts` | 对话历史、会话管理 |

### 7. 业务页面 (`views/`)
按业务模块划分的页面视图，每个目录对应一个功能模块。

| 模块 | 目录 | 包含页面 |
|------|------|----------|
| 工作台 | `dashboard/` | 资源总览、快捷入口、统计图表 |
| 模型广场 | `model/` | 模型列表、模型详情、版本对比 |
| 训练管理 | `training/` | 任务列表、任务详情、日志查看 |
| 推理服务 | `inference/` | 服务列表、服务详情、配置管理 |
| 数据集 | `dataset/` | 数据集列表、数据集详情、标注工具 |
| 监控中心 | `monitor/` | 资源监控、告警配置、用量统计 |
| 系统管理 | `system/` | 用户管理、角色管理、系统配置 |

### 8. 工具函数 (`utils/`)
项目通用工具函数，包括 HTTP 请求封装（Axios）、日期格式化、数据校验、本地存储等。

### 9. 全局配置 (`settings.ts`)
项目级别的全局配置项，如 API 基础路径、请求超时时间、分页默认值等。

### 10. 应用入口 (`main.ts`)
Vue 应用初始化入口，负责创建应用实例、注册全局插件（路由、状态管理）、挂载到 DOM。

### 11. 全局样式 (`style.css`)
项目全局 CSS 变量与基础样式，定义色彩系统、字体、响应式断点等。

---

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3 (Composition API) | ^3.5 |
| 构建工具 | Vite | ^8.2 |
| 语言 | TypeScript | ~6.0 |
| 状态管理 | Pinia | - |
| 路由 | Vue Router | - |
| HTTP 请求 | Axios | - |
| UI 组件库 | 待定 | - |
| 图表 | ECharts | - |
| 包管理 | npm | - |

---

## 开发指南

### 快速开始
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 类型检查 + 构建
npm run build

# 预览构建结果
npm run preview
```

### 命名规范
- **组件文件**：PascalCase（如 `HomePage.vue`、`AiChat.vue`）
- **TS/JS 文件**：kebab-case（如 `use-sse.ts`、`model.ts`）
- **目录**：kebab-case（如 `ai-chat/`、`file-upload/`）
- **Vue 组件**：使用 `<script setup lang="ts">` 语法
- **CSS**：使用 CSS 变量（定义在 `style.css`）保持主题一致性

### 目录约定
- `api/`：仅存放接口请求函数，不包含业务逻辑
- `components/`：存放可复用的 UI 组件，每个子目录为独立组件单元
- `hooks/`：存放 Composition API 逻辑复用，以 `use-` 前缀命名
- `stores/`：存放 Pinia Store，按业务领域拆分
- `views/`：存放路由级别的页面组件，按业务模块分目录