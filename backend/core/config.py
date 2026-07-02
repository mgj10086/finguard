"""
FinGuard 配置管理

使用 pydantic-settings 从环境变量加载配置。
支持 .env 文件自动加载。
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "FinGuard"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    APP_SECRET_KEY: str = "dev-secret-key-change-in-production"
    APP_DEBUG: bool = True

    # 数据库
    DATABASE_ENGINE: Literal["postgresql", "sqlite"] = "postgresql"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "finguard"
    DATABASE_PASSWORD: str = "finguard_secret"
    DATABASE_NAME: str = "finguard"
    DATABASE_URL: Optional[str] = None  # 手动指定完整连接串

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_ALIAS: str = "default"
    MILVUS_COLLECTION: str = "regulation_chunks"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "finguard_neo4j"

    # LLM
    LLM_BASE_URL: str = "http://localhost:8001/v1"
    LLM_API_KEY: str = "not-needed"
    LLM_MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 8192

    # 备选 LLM (fallback)
    FALLBACK_LLM_BASE_URL: Optional[str] = None
    FALLBACK_LLM_API_KEY: Optional[str] = None
    FALLBACK_LLM_MODEL_NAME: Optional[str] = None

    # 嵌入模型
    EMBEDDING_MODEL_PATH: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "finguard_minio"
    MINIO_SECRET_KEY: str = "finguard_minio_secret"
    MINIO_BUCKET: str = "regulations"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    @property
    def database_url(self) -> str:
        """获取数据库连接字符串"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.DATABASE_ENGINE == "sqlite":
            db_path = Path(__file__).parent.parent.parent / "data" / "finguard.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
