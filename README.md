# 校园智导 — 面向高校新生的 AI 校园智能导览系统

基于大模型与校园知识库的 AI 校园导览与问答系统。项目面向高校新生入学与在校生活场景，提供报到咨询、校园生活、学习教务、奖助贷、办事服务、安全防骗、校园概况与地标讲解等一站式智能问答，支持文本/语音交互与数字人展示。

## 项目简介

校园智导以“游客端 + 管理后台 + FastAPI 服务 + 校园知识库”为核心结构：

- 游客端提供文本问答、语音识别、语音播报、数字人展示、地标讲解与常见问题快捷咨询。
- 管理后台提供校园知识库、对话记录、数据统计、敏感词过滤、游客反馈分析与系统配置管理。
- 后端 AI 问答采用当前主流的 Agent（智能体）架构：由 LLM 规划器进行意图识别与任务分解，调度领域工具（结构化数据 + FAISS 向量检索）获取资料，结合会话级记忆，再由大模型生成导览回答；校园知识库与 SQLite 数据库负责运营数据管理。

## 功能模块

- AI 校园问答：基于 Agent 架构（规划器 + 工具调用 + 记忆），结合本地知识库与大模型生成导览回答。
- 多轮对话：基于会话级记忆，支持上下文拼接和连续咨询。
- 语音交互：支持 ASR 语音识别与 TTS 语音合成。
- 数字人展示：基于 Live2D 的虚拟导览形象，可配置模型、音色、语速与系统提示词。
- 地标讲解：针对校园主要地标提供图文讲解与问答。
- 知识库管理：维护校园知识、地标信息、FAQ 与未解决问题。
- 数据看板：统计访问人数、提问数量、评分、满意度与热门问题。
- 反馈分析：根据游客评价生成关注点、情绪趋势与改进建议。
- 后台权限：提供管理员登录、账号管理与操作日志。

## AI 问答 Agent 架构

AI 问答采用当前主流的 Agent（智能体）架构，由规划器、工具集、记忆与编排器四部分构成：

- **规划器 Planner**：由 LLM 驱动的意图识别与任务分解模块。接收用户问题后输出结构化 JSON 计划（意图 `intent` + 工具任务列表 `tasks`），从可用工具中挑选最匹配的检索路径。
- **工具集 Tools**：内置 9 个校园领域工具，底层基于 FAISS 向量检索：
  - `search_registration`：新生报到入学（报到流程、必带材料、缴费、一卡通、军训、体检等）
  - `search_living`：住宿与餐饮（宿舍、食堂、水电空调、快递、商超、洗浴等生活服务）
  - `search_academics`：学习与教务（课程、选课、学分、图书馆、教材、考试、学籍、培养方案）
  - `search_financial_aid`：奖助贷（奖学金、助学金、助学贷款、勤工助学、绿色通道、资助政策）
  - `search_campus_life`：校园生活（社团、活动、体育、讲座、志愿、心理、校医院、就业等）
  - `search_service`：办事服务与数字校园（证明开具、请假、补办、校园网、VPN、邮箱、统一认证）
  - `search_safety`：安全与防骗（电信诈骗、消防、紧急电话、防盗、防推销、校园贷风险）
  - `search_overview`：学校概况与地标（校史、校区、校训、地址、主要建筑）
  - `search_general`：通用检索（兜底，不限定分类）
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
[工具集] 调用领域工具（FAISS 向量检索）
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
- edge-tts / 百度 TTS（语音合成）

## 项目结构

```text
.
├── backend/                 # FastAPI 后端服务
│   ├── api/                 # API 路由
│   ├── app/                 # Agent 架构（planner/tools/memory）、知识库与 LLM 服务
│   ├── data/                # 本地数据库目录
│   ├── indexes/             # FAISS 向量索引（构建产物）
│   ├── knowledge_docs/      # 校园知识库原始文档
│   ├── models/              # SQLAlchemy 数据模型
│   ├── schemas/             # Pydantic 数据结构
│   ├── services/            # 业务服务
│   ├── main.py              # 后端入口
│   └── requirements.txt     # Python 依赖
├── frontend/                # Vue 前端项目
│   ├── public/              # 静态资源和 Live2D 模型
│   ├── src/                 # 前端源码（游客端 + 管理后台）
│   └── package.json
├── start.bat                # Windows 一键启动脚本
├── .env.example             # 环境变量示例
├── .gitignore               # Git 忽略规则
└── 部署和使用手册.md
```

## 本地运行

### 方式一：一键启动

Windows 环境下在**项目根目录**双击：

```text
start.bat
```

启动后访问：

- 游客端：http://localhost:5173 （无需登录）
- 管理后台：http://localhost:5173/login
- API 文档：http://localhost:8000/docs

默认后台账号：

```text
admin / admin123
```

> 公开演示或部署前，请务必修改默认管理员密码和 JWT 密钥。

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

## 知识库与索引

- 校园知识库原始文档位于 `backend/knowledge_docs/`，由 `splitter` 切分、`classify_chunk` 分类后写入 FAISS 索引（`backend/indexes/`）。
- 首次运行若 `backend/indexes/` 不存在，`start.bat` 会自动调用 indexer 重建索引（需联网并配置 API Key）；亦可基于 `replay_cache.json` 进入离线回放模式，保障无网络环境下常见问题仍可应答。
- 更新知识库文档后，可通过管理后台“重建知识库”或重新运行 indexer 使检索生效。

## 说明

本项目用于展示 AI 应用开发、知识库问答、Agent 智能体、前后端分离与后台管理能力。
