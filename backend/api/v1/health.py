"""健康检查 API"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "status": "healthy",
            "service": "FinGuard",
            "version": "0.1.0",
        },
        "timestamp": None,  # 由中间件填充
    }


@router.get("/health/ready")
async def readiness_check():
    """就绪检查"""
    # TODO: 检查各服务连接状态（Redis、Milvus、Neo4j、PostgreSQL）
    return {
        "code": 200,
        "message": "success",
        "data": {"ready": True},
        "timestamp": None,
    }
