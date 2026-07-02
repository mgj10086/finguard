# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@规则参见：d:/Users/Administrator/Documents/Obsidian Vault/Claude相关/项目启动宪法.md

## Project Overview

FinGuard — 金融合规文档智能审核系统。多 Agent 协同预审平台，以"分发 → 审核 → 裁决 → 复审"流水线自动解析文档、匹配法规条款、生成审核结论。目标用户：金融机构合规部门。

## 技术栈

- **LLM**: Qwen2.5-7B (LoRA 微调) + vLLM 推理服务（备选 DeepSeek-V3 API fallback）
- **Agent 编排**: LangGraph (StateGraph 四阶段流水线)
- **LLM 框架**: LangChain (LCEL RAG 链) + LlamaIndex (文档索引)
- **嵌入模型**: BGE-M3 (dense 1024d + sparse)
- **向量数据库**: Milvus (生产) / Milvus Lite (开发)
- **图数据库**: Neo4j Community (条款-违规案例-处罚结果图谱)
- **关系数据库**: PostgreSQL 16 (业务数据)
- **缓存/消息**: Redis 7 (Agent 状态传递 + Celery broker)
- **后端**: Python 3.11+ / FastAPI / Pydantic v2 / Celery
- **前端**: Vue3 Composition API / Element Plus / ECharts / Pinia / Vite
- **对象存储**: MinIO (文档存储)
- **容器化**: Docker Compose (全栈编排)
- **监控**: Prometheus + Grafana
- **微调**: LLaMA-Factory

## Commands

```bash
# 启动后端 (开发模式, 热重载)
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动 Celery worker
cd backend && celery -A core.celery_app worker --loglevel=info

# 启动前端
cd frontend && npm run dev

# Docker 全栈启动
docker-compose up -d

# 初始化数据库和种子数据
python scripts/init_db.py
python scripts/seed_data.py

# 运行测试
pytest tests/
```

## Architecture

```
请求 → FastAPI Router (backend/api/) → LangGraph Agent (backend/agents/) → Services
                                                                 ↕
                                                        Neo4j / Milvus / PostgreSQL
```

**四层分离**：
- `backend/api/` — 路由层，参数校验 + 响应格式化，调用 agent
- `backend/agents/` — LangGraph 状态图编排，业务逻辑层
- `backend/services/` — 基础设施层（RAG 引擎、知识图谱、文档解析、LLM 服务）
- `backend/skills/` — 可复用 Tool 工具（文档比对、表格抽取）

**数据流**：

```
用户上传文档 → 文档解析 (PDF/Word) → RAG 向量化
    → LangGraph 流水线:
        ① 分发 (Dispatcher) → 提取业务要素，确定审核范围
        ② 审核 (Reviewer)   → RAG 检索法规 + LLM 逐条比对
        ③ 裁决 (Adjudicator) → 知识图谱推理 + 综合判定
        ④ 复审 (Final Review)→ 结论汇总、可解释性生成
    → 写入 PostgreSQL → 返回审核报告
```

## Key Conventions

- **导入路径**：全项目使用 `backend.xxx` 绝对导入
- **API 响应格式**：统一 `{"code": 200, "message": "success", "data": {...}, "timestamp": "ISO8601"}`
- **Agent 状态模式**：LangGraph State 使用 TypedDict，所有节点接收 `GraphState` 返回 `Partial<GraphState>`
- **LLM 调用**：统一通过 `services.llm_service` 调用，支持 vLLM/Ollama/API fallback 切换
- **模型枚举**：数据库表和字段命名使用小写+下划线

## Project Structure

```
finguard/
├── backend/
│   ├── main.py                  # FastAPI app entry
│   ├── core/
│   │   ├── config.py            # 配置管理 (pydantic-settings)
│   │   ├── database.py          # PostgreSQL/SQLite 抽象
│   │   └── celery_app.py        # Celery app
│   ├── api/v1/                  # API 路由
│   │   ├── reviews.py           # 审核流水线 API
│   │   ├── documents.py         # 文档管理 API
│   │   ├── knowledge.py         # 知识库管理 API
│   │   └── health.py            # 健康检查
│   ├── agents/
│   │   ├── graph.py             # LangGraph StateGraph 定义
│   │   ├── dispatcher.py        # ① 分发节点
│   │   ├── reviewer.py          # ② 审核节点
│   │   ├── adjudicator.py       # ③ 裁决节点
│   │   └── final_reviewer.py    # ④ 复审节点
│   ├── services/
│   │   ├── llm_service.py       # LLM 统一调用接口
│   │   ├── rag_engine.py        # RAG 检索引擎
│   │   ├── knowledge_graph.py   # Neo4j 知识图谱
│   │   ├── document_parser.py   # 文档解析 (PDF/Word)
│   │   └── embedding.py         # BGE-M3 嵌入服务
│   ├── skills/
│   │   ├── doc_comparison.py    # 文档比对工具
│   │   └── table_extraction.py  # 表格抽取工具
│   └── models/
│       ├── review.py            # 审核相关模型
│       ├── document.py          # 文档模型
│       └── regulation.py        # 法规模型
├── frontend/                    # Vue3 前端
├── data/regulations/            # 法规源文件 (PDF/Word)
├── docker/                      # Dockerfile
├── scripts/                     # 工具脚本
└── tests/                       # 测试
```

## 质量优先级

功能完整度 > 代码简洁性 > token 节省 > 性能优化

## 工作方式（宪法规定，不可违反）

1. 跨文件改动（3+文件）→ 必须先 EnterPlanMode，用户确认后才写代码
2. 每次只改一个逻辑单元 → 改完验证
3. 每个小任务完成后 → 提交
4. 并行任务 → 用 Worktree 隔离
5. 遇到阻碍 → 先查 d:/Users/Administrator/Documents/Obsidian Vault/Claude相关/操作突破日志.md
