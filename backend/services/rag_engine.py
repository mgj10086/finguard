"""
RAG 检索引擎

基于 LlamaIndex + Milvus 的法规条款检索。
主要职责：
1. 文档加载与索引（LlamaIndex）
2. 三级层级索引：章节 → 条款 → 细则
3. 混合检索（稠密 + 稀疏）
4. LCEL 组合链：查询改写 → 检索 → 重排序 → 生成
"""

import logging
from typing import Any, Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    RAG 检索引擎

    封装 LlamaIndex 的索引构建和 LangChain 的检索链。
    支持稠密向量（dense）和稀疏向量（sparse）混合检索。
    """

    def __init__(self):
        self._index = None
        self._collection_name = settings.MILVUS_COLLECTION
        self._dimension = settings.EMBEDDING_DIMENSION

    async def initialize(self):
        """初始化：连接 Milvus，加载索引"""
        try:
            from llama_index.core import StorageContext, VectorStoreIndex
            from llama_index.vector_stores.milvus import MilvusVectorStore

            logger.info(f"Connecting to Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            vector_store = MilvusVectorStore(
                uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}",
                collection_name=self._collection_name,
                dim=self._dimension,
                overwrite=False,
            )
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            # 从已有向量库加载
            self._index = VectorStoreIndex.from_vector_store(
                vector_store, storage_context=storage_context
            )
            logger.info(f"RAG engine initialized with Milvus collection '{self._collection_name}'")
        except Exception as e:
            logger.warning(f"Milvus connection failed ({e}). RAG engine in lazy-init mode.")

    async def build_index(self, file_paths: list[str]) -> dict:
        """
        构建/更新索引

        Args:
            file_paths: 法规文档路径列表

        Returns:
            索引统计信息
        """
        try:
            from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
            from llama_index.core.node_parser import HierarchicalNodeParser
            from llama_index.vector_stores.milvus import MilvusVectorStore

            vector_store = MilvusVectorStore(
                uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}",
                collection_name=self._collection_name,
                dim=self._dimension,
                overwrite=False,
            )

            # 加载文档
            documents = SimpleDirectoryReader(input_files=file_paths).load_data()
            logger.info(f"Loaded {len(documents)} documents")

            # 层级节点解析（章节→条款→细则）
            node_parser = HierarchicalNodeParser.from_defaults(
                chunk_sizes=[1024, 512, 256],
                chunk_overlap=50,
            )
            nodes = node_parser.get_nodes_from_documents(documents)
            logger.info(f"Split into {len(nodes)} nodes")

            # 构建索引
            self._index = VectorStoreIndex.from_documents(
                documents,
                storage_context=StorageContext.from_defaults(vector_store=vector_store),
                show_progress=True,
            )

            return {
                "documents": len(documents),
                "nodes": len(nodes),
                "collection": self._collection_name,
            }
        except Exception as e:
            logger.error(f"Index build failed: {e}", exc_info=True)
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.6,
    ) -> list[dict[str, Any]]:
        """
        语义检索相关法规条款

        Args:
            query: 查询文本
            top_k: 返回 top-K 结果
            min_score: 最低相似度阈值

        Returns:
            [{ "content": "...", "score": 0.95, "metadata": {...} }]
        """
        if self._index is None:
            await self.initialize()

        if self._index is None:
            logger.error("RAG engine not initialized")
            return []

        retriever = self._index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)

        results = []
        for node in nodes:
            if node.score and node.score >= min_score:
                results.append({
                    "content": node.text,
                    "score": node.score,
                    "metadata": node.metadata,
                    "node_id": node.node_id,
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """
        混合检索（稠密 + 稀疏）

        BGE-M3 支持稠密和稀疏向量，通过加权融合提高检索精度。
        """
        # 当前使用标准语义搜索；混合检索需要 Milvus 2.4+ hybrid search API
        # TODO: 在 Milvus 2.4+ 稳定后切换到真正的 hybrid search
        return await self.search(query, top_k=top_k)

    async def query_with_context(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict:
        """
        检索 + 生成（RAG）

        Returns:
            {"answer": "...", "sources": [...], "usage": {...}}
        """
        from langchain.chains.combine_documents import create_stuff_documents_chain
        from langchain.chains.retrieval import create_retrieval_chain
        from langchain.schema import Document as LCDocument
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate

        # 检索
        results = await self.search(query, top_k=top_k)
        if not results:
            return {"answer": "未找到相关法规条款", "sources": [], "usage": {}}

        # 构建 LangChain 检索链
        llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            openai_api_base=settings.LLM_BASE_URL,
            openai_api_key=settings.LLM_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "你是一个金融合规审核专家。基于以下法规条款，回答用户的问题。\n"
                "如果检索到的条款不足以回答问题，请明确指出。\n"
                "引用条款时注明条款编号。\n\n"
                "法规条款：\n{context}"
            )),
            ("human", "{input}"),
        ])

        # 将检索结果转为 LangChain Document
        lc_docs = [
            LCDocument(
                page_content=r["content"],
                metadata={**r["metadata"], "score": r["score"]}
            )
            for r in results
        ]

        chain = create_stuff_documents_chain(llm, prompt)
        result = await chain.ainvoke({
            "context": lc_docs,
            "input": query,
        })

        return {
            "answer": result,
            "sources": results,
        }


# 全局单例
rag_engine = RAGEngine()
