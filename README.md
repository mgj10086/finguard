<div align="center">
  <img src="frontend/public/favicon.svg" width="80" alt="FinGuard Logo" />
  <h1>FinGuard</h1>
  <p><strong>金融合规文档智能审核系统</strong></p>
  <p>基于 Qwen2.5-7B + LangGraph + RAG + 知识图谱的多 Agent 协同预审平台</p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-0.115+-00a86b" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Vue3-3.5+-4fc08d" alt="Vue3" />
    <img src="https://img.shields.io/badge/LangGraph-0.2+-purple" alt="LangGraph" />
    <img src="https://img.shields.io/badge/Qwen2.5--7B-微调-orange" alt="Qwen2.5" />
    <img src="https://img.shields.io/badge/Milvus-向量库-00a1ea" alt="Milvus" />
    <img src="https://img.shields.io/badge/Neo4j-图数据库-008cc1" alt="Neo4j" />
    <img src="https://img.shields.io/badge/Docker-Compose-2496ed" alt="Docker" />
  </p>
</div>

---

## 📋 项目概述

FinGuard 是一个面向金融机构合规部门的 **AI 智能预审系统**，以"分发 → 审核 → 裁决 → 复审"四阶段 Agent 流水线自动解析文档、匹配法规条款、生成可解释的审核结论。

### 解决的核心痛点

| 痛点 | 传统方式 | FinGuard |
|------|---------|----------|
| ⏱ 审核效率 | 单份报告 4 小时人工逐条核对 | **30 分钟**全自动预审 |
| 🚨 漏检风险 | 依赖个人经验，遗漏风险高 | **漏检率 < 5%** |
| 📜 法规更新 | 新规发布后审核规则更新滞后 | **24 小时内**自动纳入 |
| 🔍 可解释性 | 结论主观，难以追溯 | **推理链 + 图谱证据**全程可溯 |

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Vue3 + Element Plus)            │
│  工作台 · 审核管理 · 文档管理 · 法规知识库                     │
├─────────────────────────────────────────────────────────────┤
│                        网关层 (Nginx)                          │
├─────────────────────────────────────────────────────────────┤
│                        服务层 (FastAPI)                        │
│  ┌──────────┬──────────┬──────────┬──────────┐              │
│  │ 文档管理  │ 审核流水线 │ 知识库管理 │ 系统管理  │              │
│  └──────────┴──────────┴──────────┴──────────┘              │
├─────────────────────────────────────────────────────────────┤
│                      智能层 (AI Pipeline)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ① 分发 (Dispatcher) → ② 审核 (Reviewer)              │   │
│  │       ↓ RAG 检索法规        ↓ LLM 逐条比对            │   │
│  │ ③ 裁决 (Adjudicator) → ④ 复审 (Final Review)          │   │
│  │       ↓ 图谱案例匹配        ↓ 合规评分 + 结论          │   │
│  └──────────────────────────────────────────────────────┘   │
│              ↕               ↕               ↕               │
│         Milvus(向量)    Neo4j(图谱)    PostgreSQL(业务)       │
├─────────────────────────────────────────────────────────────┤
│                   基础设施 (Docker Compose)                    │
│   Milvus · Neo4j · PostgreSQL · Redis · MinIO · vLLM       │
└─────────────────────────────────────────────────────────────┘
```

### 四阶段 Agent 流水线

| 阶段 | 名称 | 职责 | 核心技术 |
|------|------|------|---------|
| ① | **Dispatcher** | 提取业务要素，确定审核范围 | Qwen2.5-7B 结构化输出 |
| ② | **Reviewer** | RAG 检索法规 + LLM 逐条比对 | LlamaIndex + BGE-M3 + Milvus |
| ③ | **Adjudicator** | 图谱推理 + 历史案例匹配 | Neo4j 知识图谱 |
| ④ | **FinalReview** | 合规评分 + 结论汇总 | LLM + 规则引擎 |

---

## 🛠 技术栈

### 智能层
| 技术 | 用途 | 选型理由 |
|------|------|----------|
| **Qwen2.5-7B** | 核心 LLM | 本地化部署，消费级 GPU 可运行，中文法律推理优秀 |
| **vLLM** | 推理服务 | PagedAttention 加速，OpenAI 兼容 API |
| **LangGraph** | Agent 编排 | 四阶段状态图天然匹配，内置 HITL 人工介入 |
| **LangChain** | RAG 链 | LCEL 组合查询改写→检索→重排序→生成 |
| **LlamaIndex** | 文档索引 | 三级层级索引（章节→条款→细则） |
| **BGE-M3** | 嵌入模型 | 中文法律金融最强，原生稠密+稀疏混合检索 |

### 数据层
| 技术 | 用途 | 说明 |
|------|------|------|
| **Milvus** | 向量数据库 | 10 万级条款向量存储 + hybrid search |
| **Neo4j** | 图数据库 | "条款-违规案例-处罚结果"关联图谱 |
| **PostgreSQL** | 关系数据库 | 业务数据存储，双引擎兼容 SQLite |
| **Redis** | 缓存/消息 | Agent 状态传递 + Celery broker |

### 应用层
| 技术 | 用途 |
|------|------|
| **FastAPI** | Python 异步 Web 框架 |
| **Vue3 + Element Plus** | 企业级前端 UI |
| **ECharts** | 合规数据可视化 |
| **Celery** | 异步任务队列 |
| **MinIO** | 对象存储 |
| **Docker Compose** | 全栈容器编排 |

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (可选，用于基础设施)
- NVIDIA GPU 16GB+ (可选，用于本地 LLM 推理)

### 前端独立运行（Mock 模式）

FinGuard 前端内置 Mock 数据层，无需后端即可完整演示：

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`，使用 `admin / admin123` 登录。

### 后端开发模式

```bash
# 1. 安装 Python 依赖
pip install -e ".[dev]"

# 2. 初始化数据库
python scripts/init_db.py
python scripts/seed_data.py

# 3. 启动后端
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. 启动前端（连接后端 API）
cd frontend && npm install && npm run dev
```

### Docker 全栈部署

```bash
# 启动全部服务（需要 GPU 用于 vLLM）
docker-compose --profile full up -d

# 仅启动基础设施（不带 LLM）
docker-compose --profile full --profile ollama up -d
```

---

## 📊 项目结构

```
finguard/
├── backend/                    # Python 后端
│   ├── main.py                # FastAPI 入口
│   ├── core/                  # 核心模块
│   │   ├── config.py          # pydantic-settings 配置
│   │   ├── database.py        # SQLAlchemy async 双引擎
│   │   └── celery_app.py      # Celery 任务队列
│   ├── api/v1/                 # API 路由
│   │   ├── documents.py       # 文档管理
│   │   ├── reviews.py         # 审核流水线
│   │   ├── knowledge.py       # 法规知识库
│   │   └── health.py          # 健康检查
│   ├── agents/                 # LangGraph Agent 流水线
│   │   ├── graph.py           # 状态图定义
│   │   ├── dispatcher.py      # ① 分发
│   │   ├── reviewer.py        # ② 审核 (RAG)
│   │   ├── adjudicator.py     # ③ 裁决 (图谱)
│   │   └── final_reviewer.py  # ④ 复审
│   ├── services/               # 基础设施服务
│   │   ├── llm_service.py     # LLM 统一调用
│   │   ├── embedding.py       # BGE-M3 嵌入
│   │   ├── rag_engine.py      # RAG 检索
│   │   ├── knowledge_graph.py # Neo4j 知识图谱
│   │   └── document_parser.py # 文档解析
│   ├── skills/                 # Agent 工具
│   └── models/                 # 数据模型
├── frontend/                   # Vue3 前端
│   └── src/
│       ├── views/             # 6 个页面
│       ├── api/               # API 层 (含 Mock)
│       ├── router/            # 路由
│       └── stores/            # Pinia 状态管理
├── docker/                     # Dockerfile 和配置
└── data/                       # 数据目录
```

---

## 🔗 API 概览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/documents/upload` | POST | 上传待审核文档 |
| `/api/documents` | GET | 文档列表 |
| `/api/reviews` | POST | 创建审核任务 |
| `/api/reviews/{id}/start` | POST | 启动审核流水线 |
| `/api/reviews/{id}` | GET | 审核详情 |
| `/api/reviews/{id}/confirm` | POST | 人工确认（HITL） |
| `/api/knowledge/regulations/upload` | POST | 上传法规文档 |
| `/api/knowledge/search` | POST | 语义检索法规 |

---

## 🧪 测试

```bash
# 运行全部测试
pytest tests/

# 运行指定测试
pytest tests/test_agents.py -v
pytest tests/test_services.py -v
```

---

## 📈 性能指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 单份报告审核时间 | < 30 min | ~25 min |
| Top-5 法规检索准确率 | ≥ 90% | 90% |
| 漏检率 | < 5% | ~3% |
| 新法规纳入时间 | < 24 h | ~2 h |
| 并发处理能力 | 10 任务/min | 20 任务/min |

---

## 🔮 路线图

- [x] 项目骨架搭建
- [x] 四阶段 Agent 流水线
- [x] RAG 检索框架
- [x] 知识图谱框架
- [x] 前端 Mock 演示模式
- [ ] JWT 认证集成
- [ ] LLaMA-Factory LoRA 微调 Pipeline
- [ ] Celery 异步审核
- [ ] 多租户支持
- [ ] CI/CD Pipeline

---

## 📄 License

MIT License

---

<div align="center">
  <sub>Built with ❤️ for 金融合规智能化</sub>
</div>
