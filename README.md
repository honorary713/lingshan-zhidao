# 灵山智导

基于大模型与景区知识库的 AI 数字人导览系统。项目面向景区游客咨询和后台运营管理，支持游客问答、语音交互、知识库维护、对话记录、数据统计、敏感词过滤、游客反馈分析等功能。

## 项目简介

灵山智导以“游客端 + 管理后台 + FastAPI 服务 + 景区知识库”为核心结构：

- 游客端提供文本问答、语音识别、语音播报、数字人展示和常见问题快捷咨询。
- 管理后台提供景区、景点、FAQ、敏感词、黑名单、对话记录、未解决问题、数据看板和系统配置管理。
- 后端 AI 问答采用当前主流的 **Agent（智能体）架构**：由 LLM 规划器进行意图识别与任务分解，调度领域工具（结构化数据 + FAISS 向量检索）获取资料，结合会话级记忆，再由大模型生成导览回答；知识库与 SQLite 数据库负责运营数据管理。

## 功能模块

- AI 景区问答：基于 Agent 架构（规划器 + 工具调用 + 记忆），结合本地知识库与大模型生成导览回答。
- 多轮对话：基于会话级记忆，支持上下文拼接和连续咨询。
- 语音交互：支持 ASR 语音识别与 TTS 语音合成。
- 数字人配置：支持模型、音色、语速、系统提示词等参数配置。
- 知识库管理：维护景区信息、景点信息、FAQ 和未解决问题。
- 数据看板：统计访问人数、提问数量、评分、满意度和热门问题。
- 反馈分析：根据游客评价生成关注点、情绪趋势和改进建议。
- 后台权限：提供管理员登录、账号管理和操作日志。

## AI 问答 Agent 架构

AI 问答已从传统 RAG 流水线升级为当前主流的 **Agent（智能体）架构**，由规划器、工具集、记忆与编排器四部分构成：

- **规划器 Planner**：由 LLM 驱动的意图识别与任务分解模块。接收游客问题后输出结构化 JSON 计划（意图 `intent` + 工具任务列表 `tasks`），从可用工具中挑选最匹配的检索路径。
- **工具集 Tools**：内置 5 个领域工具，底层基于结构化数据与 FAISS 向量检索：
  - `search_scenic_spot`：景点结构化查询（灵山大佛、梵宫、五印坛城等）
  - `search_history_culture`：历史文化、佛教渊源、建筑背景
  - `query_ticket`：门票价格、优惠、半价免票、联票与观光车
  - `recommend_route`：按兴趣推荐游览路线与行程
  - `practical_info`：餐饮、开放时间、交通、住宿等实用信息
- **记忆 Memory**：基于 `session_id` 的会话级多轮记忆（默认保留最近 20 条消息），让连续咨询具备上下文。
- **编排器 Agent**：执行“规划 → 调用工具 → 聚合检索上下文 → LLM 撰写最终回答”的闭环，并保留敏感词过滤与未解决问题兜底。

问答执行流程：

```text
游客问题
   │
   ▼
[规划器] 意图识别 + 任务分解 → tasks
   │
   ▼
[工具集] 调用领域工具（结构化数据 + FAISS 向量检索）
   │
   ▼
[上下文聚合] 拼接检索到的参考资料
   │
   ▼
[LLM] 基于参考资料生成口语化导览回答
   │
   ▼
[记忆] 写入本轮对话 → 返回游客端
```

## 技术栈

前端：

- Vue 3
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios
- ECharts
- Pixi.js / Live2D

后端：

- Python
- FastAPI
- SQLAlchemy / SQLite
- FAISS 向量检索
- 自研 Agent 框架（Planner / Tools / Memory 编排）
- OpenAI 兼容 API（function calling 风格工具调用）
- LangChain（文本切分与 Embedding 适配）
- edge-tts / DashScope / 百度 ASR 相关能力

## 项目结构

```text
.
├── backend/                 # FastAPI 后端服务
│   ├── api/                 # API 路由
│   ├── app/                 # Agent 架构（planner/tools/memory）、知识库与 LLM 服务
│   ├── data/                # 本地数据库目录，默认不提交
│   ├── models/              # SQLAlchemy 数据模型
│   ├── schemas/             # Pydantic 数据结构
│   ├── services/            # 业务服务
│   ├── main.py              # 后端入口
│   └── requirements.txt     # Python 依赖
├── frontend/                # Vue 前端项目
│   ├── public/              # 静态资源和 Live2D 模型
│   ├── src/                 # 前端源码
│   └── package.json
├── start.bat                # Windows 一键启动脚本
├── .env.example             # 环境变量示例
├── .gitignore               # Git 忽略规则
└── GitHub上传指南.md
```

## 本地运行

### 方式一：一键启动

Windows 环境下可以双击：

```text
start.bat
```

启动后访问：

- 游客端：http://localhost:5173
- 管理后台：http://localhost:5173/login
- API 文档：http://localhost:8000/docs

默认后台账号：

```text
admin / admin123
```

> 首次公开部署或演示前，请务必修改默认管理员密码和 JWT 密钥。

### 方式二：手动启动

启动后端：

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

启动前端：

```bash
cd frontend
npm install
npm run dev
```

## 说明

本项目主要用于展示 AI 应用开发、知识库问答、前后端分离、后台管理和数据统计能力。
