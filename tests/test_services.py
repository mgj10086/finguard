"""服务层单元测试"""

import pytest


@pytest.mark.asyncio
async def test_llm_service_import():
    """测试 LLM 服务导入"""
    from backend.services.llm_service import LLMService
    svc = LLMService()
    assert svc is not None


@pytest.mark.asyncio
async def test_document_parser_import():
    """测试文档解析器导入"""
    from backend.services.document_parser import DocumentParser
    parser = DocumentParser()
    assert parser is not None


@pytest.mark.asyncio
async def test_rag_engine_import():
    """测试 RAG 引擎导入"""
    from backend.services.rag_engine import RAGEngine
    engine = RAGEngine()
    assert engine is not None


@pytest.mark.asyncio
async def test_knowledge_graph_import():
    """测试知识图谱客户端导入"""
    from backend.services.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    assert kg is not None


@pytest.mark.asyncio
async def test_embedding_service_import():
    """测试嵌入服务导入"""
    from backend.services.embedding import EmbeddingService
    svc = EmbeddingService(use_local=False)
    assert svc is not None
