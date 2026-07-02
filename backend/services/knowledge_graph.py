"""
Neo4j 知识图谱服务

构建"条款-违规案例-处罚结果"关联图谱，支持审核结论追溯。
通过 Cypher 查询提供：
- 条款相关违规案例查询
- 相似案例匹配
- 审核结论证据链追溯
"""

import logging
from typing import Any, Optional

from neo4j import AsyncGraphDatabase, AsyncManagedTransaction
from neo4j.exceptions import ServiceUnavailable

from backend.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Neo4j 知识图谱客户端"""

    def __init__(self):
        self._driver = None

    async def initialize(self):
        """连接 Neo4j 数据库"""
        try:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            await self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j: {settings.NEO4J_URI}")
        except ServiceUnavailable as e:
            logger.warning(f"Neo4j connection failed: {e}. Graph features disabled.")

    async def close(self):
        """关闭连接"""
        if self._driver:
            await self._driver.close()

    async def _run_query(
        self, query: str, params: Optional[dict] = None
    ) -> list[dict[str, Any]]:
        """执行 Cypher 查询"""
        if not self._driver:
            logger.warning("Neo4j not connected, skipping query")
            return []

        async with self._driver.session(database="neo4j") as session:
            result = await session.run(query, params or {})
            records = await result.data()
            return records

    async def create_regulation_node(self, regulation: dict) -> None:
        """创建法规节点"""
        query = """
        MERGE (r:Regulation {id: $id})
        SET r.title = $title,
            r.source = $source,
            r.status = $status,
            r.updated_at = timestamp()
        """
        await self._run_query(query, regulation)

    async def create_clause_node(self, clause: dict) -> None:
        """创建条款节点，并与法规关联"""
        query = """
        MATCH (r:Regulation {id: $regulation_id})
        MERGE (c:Clause {id: $id})
        SET c.content = $content,
            c.order_num = $order_num,
            c.risk_level = $risk_level
        MERGE (r)-[:CONTAINS]->(c)
        """
        await self._run_query(query, clause)

    async def create_violation_case(self, case: dict) -> None:
        """创建违规案例节点，并关联条款"""
        query = """
        MATCH (c:Clause {id: $clause_id})
        MERGE (v:ViolationCase {id: $id})
        SET v.title = $title,
            v.description = $description,
            v.penalty = $penalty,
            v.institution = $institution_name,
            v.year = $year
        MERGE (c)-[:VIOLATED_BY]->(v)
        """
        await self._run_query(query, case)

    async def create_review_finding(self, finding: dict) -> None:
        """创建审核结论节点，关联条款和案例"""
        query = """
        MERGE (f:Finding {id: $id})
        SET f.title = $title,
            f.severity = $severity,
            f.description = $description,
            f.created_at = timestamp()
        WITH f
        OPTIONAL MATCH (c:Clause {id: $clause_id})
        FOREACH(_ IN CASE WHEN c IS NOT NULL THEN [1] ELSE [] END |
            MERGE (f)-[:CITES]->(c)
        )
        OPTIONAL MATCH (v:ViolationCase {id: $case_id})
        FOREACH(_ IN CASE WHEN v IS NOT NULL THEN [1] ELSE [] END |
            MERGE (f)-[:MATCHES]->(v)
        )
        """
        await self._run_query(query, finding)

    async def search_similar_cases(
        self, description: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        根据描述检索相似违规案例

        使用全文索引或简单关键词匹配。
        """
        query = """
        CALL db.index.fulltext.queryNodes('case_text', $query, {limit: $limit})
        YIELD node, score
        OPTIONAL MATCH (node)-[:VIOLATED_BY]-(c:Clause)
        RETURN node.title AS title,
               node.description AS description,
               node.penalty AS penalty,
               node.institution AS institution,
               c.order_num AS clause_num,
               score
        ORDER BY score DESC
        """
        # 简化为关键词搜索
        keywords = " OR ".join(description[:200].split()[:10])
        return await self._run_query(
            query, {"query": keywords, "limit": limit}
        )

    async def get_clause_evidence_chain(
        self, clause_id: str
    ) -> dict[str, Any]:
        """
        获取条款的完整证据链：
        法规 → 条款 → 违规案例 → 处罚结果
        """
        query = """
        MATCH (r:Regulation)-[:CONTAINS]->(c:Clause {id: $clause_id})
        OPTIONAL MATCH (c)-[:VIOLATED_BY]->(v:ViolationCase)
        RETURN r.title AS regulation_title,
               c.content AS clause_content,
               c.order_num AS clause_num,
               collect(DISTINCT {
                   case_title: v.title,
                   description: v.description,
                   penalty: v.penalty,
                   institution: v.institution
               }) AS violation_cases
        """
        results = await self._run_query(query, {"clause_id": clause_id})
        return results[0] if results else {}

    async def get_finding_trace(
        self, finding_id: str
    ) -> list[dict[str, Any]]:
        """
        审核结论追溯：从结论出发，追踪引用了哪些条款、匹配了什么案例
        """
        query = """
        MATCH (f:Finding {id: $finding_id})-[r]->(target)
        RETURN f.title AS finding_title,
               type(r) AS relationship,
               labels(target) AS target_type,
               CASE
                   WHEN 'Clause' IN labels(target) THEN target.content
                   WHEN 'ViolationCase' IN labels(target) THEN target.title
               END AS target_content,
               target.id AS target_id
        """
        return await self._run_query(query, {"finding_id": finding_id})


# 全局单例
knowledge_graph = KnowledgeGraph()
