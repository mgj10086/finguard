"""
阶段 2: 审核 (Reviewer)

职责：
1. 基于审核范围，逐条检索相关法规条款（RAG）
2. 对比文档内容与法规要求，发现差异
3. 生成初步审核发现

输入: document_text, review_scope, relevant_regulations
输出: clause_matches, retrieved_chunks, reviewer_findings
"""

import asyncio
import logging
from typing import Any

from backend.agents.graph import GraphState
from backend.services.llm_service import llm_service
from backend.services.rag_engine import rag_engine

logger = logging.getLogger(__name__)


class ReviewerNode:
    """审核节点"""

    @staticmethod
    async def run(state: GraphState) -> dict[str, Any]:
        """执行审核阶段"""
        document_text = state.get("document_text", "")
        review_scope = state.get("review_scope", [])
        relevant_regulations = state.get("relevant_regulations", [])
        review_id = state.get("review_id")

        logger.info(
            f"[Reviewer] Review {review_id}: 开始审核阶段, "
            f"审核范围={len(review_scope)}项"
        )

        if not review_scope:
            logger.warning(f"[Reviewer] Review {review_id}: 无审核范围，跳过")
            return {
                "clause_matches": [],
                "retrieved_chunks": [],
                "reviewer_findings": [],
                "stage_history": ["[Reviewer] 无审核范围，跳过"],
            }

        # 逐项审核（并行处理各审核范围）
        tasks = [
            ReviewerNode._review_area(area, document_text)
            for area in review_scope
        ]
        area_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 汇总结果
        all_findings = []
        all_chunks = []
        for result in area_results:
            if isinstance(result, Exception):
                logger.error(f"Area review failed: {result}")
                continue
            findings = result.get("findings", [])
            chunks = result.get("chunks", [])
            all_findings.extend(findings)
            all_chunks.extend(chunks)

        # 去重（相同条款 + 相同问题的合并）
        seen = set()
        deduplicated = []
        for f in all_findings:
            key = (f.get("clause_num", ""), f.get("title", ""))
            if key not in seen:
                seen.add(key)
                deduplicated.append(f)

        logger.info(
            f"[Reviewer] Review {review_id}: "
            f"发现 {len(deduplicated)} 个问题 "
            f"(原始 {len(all_findings)}，去重后)"
        )

        return {
            "clause_matches": deduplicated,
            "retrieved_chunks": all_chunks,
            "reviewer_findings": deduplicated,
            "stage_history": [
                f"[Reviewer] 完成 {len(review_scope)} 项审核, "
                f"发现 {len(deduplicated)} 个问题"
            ],
        }

    @staticmethod
    async def _review_area(
        area: dict, document_text: str
    ) -> dict:
        """
        审核单个业务领域

        Args:
            area: {"area": "...", "priority": "high", "focus_points": [...]}
            document_text: 文档全文

        Returns:
            {"findings": [...], "chunks": [...]}
        """
        area_name = area.get("area", "unknown")
        focus_points = area.get("focus_points", [])

        # Step 1: RAG 检索相关法规条款
        query = f"{area_name} 合规要求 {', '.join(focus_points[:3])}"
        chunks = await rag_engine.search(query, top_k=5, min_score=0.6)

        if not chunks:
            logger.info(f"[Reviewer] 领域 '{area_name}': 未检索到相关法规")
            return {"findings": [], "chunks": []}

        # Step 2: LLM 对比分析
        chunk_texts = "\n\n---\n\n".join([
            f"[条款 {i+1}] (相似度:{c['score']:.2f})\n{c['content']}"
            for i, c in enumerate(chunks)
        ])

        prompt = (
            f"你是一个金融合规审核专家。请基于以下法规条款，对比分析报告内容的合规性。\n\n"
            f"=== 审核领域 ===\n{area_name}\n"
            f"重点关注: {', '.join(focus_points)}\n\n"
            f"=== 相关法规条款 ===\n{chunk_texts}\n\n"
            f"=== 报告内容（相关部分）===\n{document_text[:6000]}\n\n"
            f"请找出报告内容与法规要求不符的地方。\n"
            f"如果没有发现违规，返回空数组 findings。\n"
            f"如果有发现，每项请包含: title(问题简述), description(详细描述), "
            f"severity(critical/high/medium/low), "
            f"source_text(原文引用), regulation_cited(引用法规), "
            f"clause_num(条款号), suggestion(整改建议)"
        )

        FINDINGS_SCHEMA = {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low"],
                            },
                            "source_text": {"type": "string"},
                            "regulation_cited": {"type": "string"},
                            "clause_num": {"type": "string"},
                            "suggestion": {"type": "string"},
                        },
                        "required": ["title", "description", "severity"],
                    },
                }
            },
            "required": ["findings"],
        }

        try:
            result = await llm_service.chat_structured(
                messages=[{"role": "user", "content": prompt}],
                output_schema=FINDINGS_SCHEMA,
            )
            findings = result.get("findings", [])
        except Exception as e:
            logger.error(f"Review analysis failed for '{area_name}': {e}")
            findings = []

        return {"findings": findings, "chunks": chunks}
