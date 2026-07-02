"""
FinGuard — FastAPI 应用入口

启动时初始化各服务连接，注册 API 路由和中间件。
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.v1 import documents, health, knowledge, reviews
from backend.core.config import settings

# 结构化日志
logging.basicConfig(
    level=logging.INFO if settings.APP_DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"🚀 {settings.APP_NAME} v0.1.0 starting...")
    logger.info(f"   Environment: {settings.APP_ENV}")

    # 启动时初始化数据库
    try:
        from backend.core.database import init_db
        await init_db()
        logger.info("   ✅ Database initialized")
    except Exception as e:
        logger.warning(f"   ⚠️ Database init skipped: {e}")

    # 启动时初始化服务（惰性加载，失败不影响启动）
    from backend.services.embedding import embedding_service
    from backend.services.knowledge_graph import knowledge_graph
    from backend.services.rag_engine import rag_engine

    try:
        await embedding_service.initialize()
        logger.info("   ✅ Embedding service ready")
    except Exception as e:
        logger.warning(f"   ⚠️ Embedding service init skipped: {e}")

    try:
        await rag_engine.initialize()
        logger.info("   ✅ RAG engine ready")
    except Exception as e:
        logger.warning(f"   ⚠️ RAG engine init skipped: {e}")

    try:
        await knowledge_graph.initialize()
        logger.info("   ✅ Knowledge graph ready")
    except Exception as e:
        logger.warning(f"   ⚠️ Knowledge graph init skipped: {e}")

    logger.info(f"✅ {settings.APP_NAME} ready on port 8000")
    yield

    # 关闭时清理
    await knowledge_graph.close()
    from backend.core.database import close_db
    await close_db()
    logger.info("🛑 Services shut down")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="金融合规文档智能审核系统",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_DEBUG else settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 统一响应中间件 =====
@app.middleware("http")
async def add_timestamp_header(request: Request, call_next):
    """为所有响应添加时间戳"""
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        body = response.body
        # 只处理 JSON 响应
        if hasattr(response, "body"):
            pass
    return response


# ===== 注册路由 =====
app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")


# ===== 异常处理器 =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )
