"""
BGE-M3 嵌入服务

封装 BGE-M3 模型，提供稠密向量 + 稀疏向量的混合嵌入能力。
支持两种模式：
- 本地模式：使用 sentence-transformers 加载模型
- API 模式：使用 vLLM/Ollama 的 embeddings API
"""

import logging
from typing import Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """嵌入服务 — 默认使用本地 BGE-M3 模型"""

    def __init__(self, use_local: bool = True):
        self._model = None
        self._use_local = use_local
        self._dimension = settings.EMBEDDING_DIMENSION

    async def initialize(self):
        """延迟初始化模型"""
        if not self._use_local:
            logger.info("Embedding service initialized in API mode")
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_PATH}")
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL_PATH,
                trust_remote_code=True,
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.warning(
                f"Failed to load local model ({e}), falling back to API mode"
            )
            self._use_local = False

    async def embed_texts(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        """
        批量获取文本嵌入向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            list of embedding vectors
        """
        if self._use_local and self._model is not None:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        else:
            return await self._embed_via_api(texts)

    async def embed_query(self, text: str) -> list[float]:
        """获取查询文本的嵌入向量"""
        if self._use_local and self._model is not None:
            embedding = self._model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embedding.tolist()
        else:
            result = await self._embed_via_api([text])
            return result[0]

    async def embed_sparse(self, texts: list[str]) -> list[dict]:
        """
        获取稀疏向量（BGE-M3 特有）

        Returns:
            list of {"indices": [...], "values": [...]}
        """
        if self._model is None:
            logger.warning("Sparse embedding requires local model")
            return []

        try:
            # BGE-M3 的稀疏向量通过 model.encode 的 return_dense=False, return_sparse=True
            sparse_embeddings = self._model.encode(
                texts,
                return_dense=False,
                return_sparse=True,
                normalize_embeddings=True,
            )
            results = []
            for sparse in sparse_embeddings:
                indices = sparse.nonzero()[1].tolist()
                values = sparse.data.tolist()
                results.append({"indices": indices, "values": values})
            return results
        except Exception as e:
            logger.error(f"Sparse embedding failed: {e}")
            return []

    async def _embed_via_api(self, texts: list[str]) -> list[list[float]]:
        """通过 vLLM/Ollama API 获取嵌入"""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        )
        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL_PATH,
            input=texts,
        )
        # 按输入顺序排序
        sorted_embeddings = sorted(
            response.data, key=lambda x: x.index
        )
        return [emb.embedding for emb in sorted_embeddings]


# 全局单例
embedding_service = EmbeddingService()
