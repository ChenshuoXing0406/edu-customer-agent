# AI 教育课程客服 Agent

## 项目简介

基于 FastAPI + 知识库检索 + 人机协同的教育课程客服系统。

系统面向在线教育课程咨询场景，支持课程介绍、价格、试听、退款、账号和证书等常见问题。用户提问后，系统先识别意图并检索知识库，再生成严格基于知识库的回答；当知识库未命中，或问题涉及退款、投诉、账号异常和人工请求时，系统会自动进入转人工流程。

项目默认使用规则式回答，可选接入 OpenAI-compatible LLM 生成更自然的客服回复。后台支持知识库补充、工单处理、满意度反馈和运营分析，形成从“发现问题”到“补充知识”的完整闭环。

## 核心功能

- AI 客服聊天
- 知识库检索问答
- 未命中问题收集
- 知识库管理
- 转人工工单
- 工单处理闭环
- 用户满意度反馈
- 运营分析后台
- Docker 部署

## 技术栈

| 分类 | 技术 |
| --- | --- |
| Web API | FastAPI |
| ORM | SQLAlchemy |
| 数据库 | SQLite / PostgreSQL |
| 前端 | HTML / CSS / JavaScript |
| 容器化 | Docker / Docker Compose |
| 云部署 | Railway |
| 模型能力 | OpenAI-compatible LLM，可选 |
| 测试 | pytest / FastAPI TestClient |

## 系统架构

```mermaid
flowchart TD
    U[用户] --> CHAT[聊天页面]
    A[运营人员] --> LOGIN[后台登录]
    LOGIN --> ADMIN[运营分析后台]
    LOGIN --> KADMIN[知识库管理页]

    CHAT --> API[FastAPI API 层]
    ADMIN --> API
    KADMIN --> API

    API --> CS[Chat Service]
    API --> KS[Knowledge Service]
    API --> TS[Ticket Service]
    API --> FS[Feedback Service]
    API --> AS[Analytics Service]

    CS --> INTENT[意图识别]
    CS --> KS
    KS --> RETRIEVE[混合知识库检索]
    RETRIEVE --> DB[(SQLite / PostgreSQL)]

    CS --> RULE[规则式回答]
    CS --> LLM[OpenAI-compatible LLM]
    LLM --> FALLBACK[异常时回退规则式回答]
    FALLBACK --> RULE

    CS --> MISS{可靠命中?}
    MISS -- 否 --> UNANSWERED[记录未命中问题]
    MISS -- 否 --> TS
    CS --> RISK{敏感问题?}
    RISK -- 是 --> TS
    TS --> DB
    FS --> DB
    AS --> DB
    KADMIN --> KS
```

## 业务流程

### 混合检索策略

系统不是简单地按单个关键词返回文档，而是综合以下信号进行打分：

1. 基础关键词召回。
2. 标题命中额外加权。
3. 课程实体匹配加权，例如 `Python`、`AI 大模型`。
4. 用户意图与知识库 `category` 匹配加权。
5. 对“课程”“报名”“适合”等弱关键词降权，避免误召回。
6. 使用可靠命中阈值过滤低质量结果。
7. 按相关度排序后返回 `top_k` 条知识。
8. 没有可靠命中时记录到 `unanswered_questions`，并建议转人工。

课程实体根据知识库动态识别。运营人员新增日语课程后，用户再次询问日语课程即可命中，不需要修改代码。

### 人机协同

以下情况会创建转人工工单：

- 知识库没有可靠命中。
- 用户明确请求人工客服。
- 用户咨询退款、退费。
- 用户出现投诉或强烈负面情绪。

客服后台可以查看工单并标记为已处理，形成工单处理闭环。

### LLM 回退机制

- 未配置 `LLM_API_KEY`：使用本地规则式回答。
- 配置模型服务：使用检索到的知识库内容生成自然语言回答。
- 知识库未命中：不调用模型，直接建议转人工。
- 模型调用失败：自动回退规则式回答。
- 敏感问题若模型遗漏转人工提示，服务端会自动补充提示。

## 页面入口

| 页面 | 地址 | 说明 |
| --- | --- | --- |
| 用户聊天页 | `/` | 面向用户的课程客服聊天页面 |
| 后台登录 | `/login` | 运营后台登录页面 |
| 运营分析后台 | `/admin` | 查看会话、工单、反馈和运营指标 |
| 知识库管理 | `/knowledge-admin` | 查看未命中问题并补充知识 |
| OpenAPI 文档 | `/docs` | FastAPI Swagger 文档 |

`/admin` 和 `/knowledge-admin` 需要登录。聊天页 `/` 与接口文档 `/docs` 保持公开访问。

## API 列表

### 页面与认证

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 用户聊天页面 |
| GET | `/login` | 后台登录页面 |
| POST | `/login` | 提交后台登录 |
| GET | `/logout` | 退出登录 |
| GET | `/admin` | 运营分析后台，需要登录 |
| GET | `/knowledge-admin` | 知识库管理页，需要登录 |
| GET | `/health` | 健康检查 |

### 业务接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/chat` | 提交用户问题，返回回答、意图、来源和转人工状态 |
| GET | `/api/conversations` | 查询聊天记录 |
| GET | `/api/handoff-tickets` | 查询转人工工单 |
| POST | `/api/handoff-tickets/{ticket_id}/resolve` | 标记工单为已处理 |
| GET | `/api/unanswered-questions` | 查询未命中问题 |
| GET | `/api/knowledge` | 查询知识库内容 |
| POST | `/api/knowledge` | 新增知识库内容 |
| POST | `/api/feedback` | 提交满意度反馈 |
| GET | `/api/feedback-stats` | 查询满意度统计 |
| GET | `/api/analytics` | 查询运营分析数据 |

## 项目结构

```text
.
├── Dockerfile
├── docker-compose.yml
├── railway.json
├── README.md
└── backend/
    ├── requirements.txt
    ├── .env.example
    ├── app/
    │   ├── main.py
    │   ├── models.py
    │   ├── api/
    │   ├── core/
    │   ├── data/
    │   ├── schemas/
    │   ├── services/
    │   └── static/
    └── tests/
```

## 环境变量

复制示例配置：

```powershell
Copy-Item backend/.env.example backend/.env
```

可用环境变量：

| 变量 | 是否必填 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | 否 | 数据库连接地址，未配置时默认使用本地 SQLite |
| `LLM_BASE_URL` | 否 | OpenAI-compatible 服务地址 |
| `LLM_API_KEY` | 否 | 模型服务密钥，未配置时回退规则式回答 |
| `LLM_MODEL` | 否 | 模型名称 |
| `ADMIN_USERNAME` | 否 | 后台账号，默认 `admin` |
| `ADMIN_PASSWORD` | 否 | 后台密码，默认 `admin123` |
| `SESSION_SECRET_KEY` | 生产必填 | Session cookie 签名密钥 |
| `PORT` | 部署平台注入 | 服务监听端口，默认 `8000` |

请勿将真实 API key、后台密码和生产环境 `SESSION_SECRET_KEY` 提交到代码仓库。

## 数据库配置

### 本地 SQLite

未配置 `DATABASE_URL` 时，系统默认使用：

```text
backend/app/data/app.db
```

首次启动时会自动创建数据表，并将 `backend/app/data/knowledge_base.json` 中的初始知识写入数据库。

### PostgreSQL

生产环境推荐使用 PostgreSQL：

```dotenv
DATABASE_URL=postgresql://username:password@host:5432/database_name
```

系统也兼容 Railway 常见的 `postgres://` 地址，并会自动使用 `psycopg` 驱动连接 PostgreSQL。

## 本地启动

建议使用 Python 3.10 或更高版本。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后访问：

- 聊天页面：http://127.0.0.1:8000/
- 后台登录：http://127.0.0.1:8000/login
- 接口文档：http://127.0.0.1:8000/docs

本地开发默认后台账号：

```text
admin / admin123
```

## Docker 启动

项目根目录提供了 `Dockerfile` 和 `docker-compose.yml`。SQLite 数据目录会绑定挂载到容器内的 `/app/app/data`，因此本地 `app.db` 会在容器重建后继续保留。

```powershell
docker compose up --build -d
```

查看日志：

```powershell
docker compose logs -f
```

停止服务：

```powershell
docker compose down
```

也可以直接从仓库根目录构建镜像：

```powershell
docker build -t edu-customer-agent .
```

容器启动命令：

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Railway 部署

仓库根目录提供了 `Dockerfile` 和 `railway.json`，Railway 可以直接从 GitHub 仓库完成构建和部署。

### 部署步骤

1. 将项目推送到 GitHub 仓库。
2. 登录 Railway，创建 `New Project`。
3. 选择 `Deploy from GitHub repo`，并关联项目仓库。
4. 点击 `+ New` 添加 PostgreSQL 服务。
5. 在应用服务中配置环境变量：

```dotenv
DATABASE_URL=${{Postgres.DATABASE_URL}}
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-admin-password
SESSION_SECRET_KEY=replace-with-a-random-secret
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=your-model-name
```

6. 等待部署完成，在 Railway 中生成公网域名。
7. 访问 Railway 生成的公网域名。

### SQLite 限制

SQLite 适合本地开发，但 Railway 容器的本地文件系统不适合作为长期生产数据存储：

- 重新部署或重建实例时，本地 `app.db` 可能丢失。
- 多实例运行时，无法可靠共享同一个 SQLite 文件。
- 并发写入能力有限。

生产环境建议使用 Railway PostgreSQL。若短期内继续使用 SQLite，需要为 `/app/app/data` 配置持久化 Volume。

## 运行测试

测试使用独立的临时 SQLite 数据库，不会修改本地 `backend/app/data/app.db`。

```powershell
cd backend
pip install -r requirements.txt
pytest
```

当前测试覆盖：

- 健康检查。
- 聊天、知识检索和未命中记录。
- Python、AI 大模型、退款、日语课程检索场景。
- 动态新增知识后重新命中。
- 转人工工单创建和处理。
- 用户反馈与运营统计。
- 后台登录、退出和环境变量账号。
- LLM 调用、失败回退和无 key 回退。
- SQLite / PostgreSQL 连接配置和模型兼容性。

## 面试讲解稿

### 项目背景

这个项目模拟在线教育平台的课程客服系统。真实业务里，大量用户会重复咨询课程适合人群、价格、试听、退款和账号问题。如果全部依赖人工客服，响应速度和服务成本都不理想；如果直接让大模型自由回答，又容易出现编造政策或错误承诺。

因此，我设计了一个“知识库检索优先、模型生成可选、敏感问题转人工”的客服 Agent。系统既能自动回答高频问题，也保留人工处理复杂问题的出口。

### 技术难点

第一个难点是控制误召回。教育客服问题中，“课程”“报名”“适合”这类词非常常见，如果只做简单关键词匹配，很容易把无关课程召回。我的做法是实现混合评分：综合关键词、标题、课程实体和意图分类，同时降低弱关键词权重，并设置可靠命中阈值。

第二个难点是控制模型幻觉。LLM 只在知识库已经可靠命中时调用，Prompt 明确要求只能根据知识库回答。知识库未命中时，系统不会让模型自由发挥，而是直接说不知道并建议转人工。模型服务异常时也会自动回退规则式回答。

第三个难点是兼顾本地开发和生产部署。本地默认使用 SQLite，不需要额外安装数据库；生产环境通过 `DATABASE_URL` 切换 PostgreSQL。Dockerfile 支持 Railway 注入的 `PORT`，仓库可以直接从根目录构建和部署。

### RAG 检索策略

检索链路可以概括为：

1. 对用户问题做意图识别。
2. 从知识库中做基础关键词召回。
3. 对标题命中和课程实体命中额外加权。
4. 对意图与知识分类一致的文档加权。
5. 对弱关键词降权。
6. 使用阈值过滤低质量结果。
7. 返回相关度最高的 `top_k` 条知识。
8. 如果没有可靠结果，记录未命中问题并转人工。

这个策略比简单关键词匹配更稳定，同时保持实现轻量，适合作为小型 RAG 系统的第一版。

### 人机协同设计

我没有把自动回答率作为唯一目标，而是把“回答正确”放在前面。退款、投诉、账号异常和明确人工请求都会进入转人工流程。即使知识库里有相关政策，系统也只先做解释，然后创建工单交给人工确认。

后台可以查看待处理工单、处理工单并保留状态，避免用户问题在自动客服和人工客服之间丢失。

### 运营闭环设计

系统会收集两类信号：

- 未命中问题：帮助运营发现知识库缺口。
- 用户满意度反馈：帮助判断回答质量。

运营人员可以在知识库管理页查看未命中问题，并直接新增知识。新增内容会立即进入后续检索流程。例如，日语课程原本未命中，补充知识后再次提问即可命中。

运营分析后台还会展示咨询量、自动解决率、转人工率、工单状态、意图分布和高频未命中问题，形成持续优化知识库的闭环。

### 后续优化方向

1. 使用向量数据库和 Embedding 检索，提升语义召回能力。
2. 引入全文检索或 BM25，与当前规则打分组合成更完整的 Hybrid Search。
3. 使用 Alembic 管理数据库迁移。
4. 为后台 API 增加更细粒度的权限控制。
5. 增加会话上下文、多轮对话和客服 SLA。
6. 增加 Prometheus 指标、结构化日志和告警。
7. 增加真实 PostgreSQL 测试环境和 CI/CD 流水线。
