"""
阶段 1: 分发 (Dispatcher)

职责：
1. 解析文档全文，提取业务要素（报告主体、期间、类型等）
2. 确定审核范围（哪些业务领域需要审核）
3. 识别相关法规（基于业务要素匹配）
4. 设定审核优先级和关注点

输入: document_text, business_type
输出: business_elements, review_scope, relevant_regulations, dispatcher_notes
"""

import json
import logging
from typing import Any

from backend.agents.graph import GraphState
from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)

# 业务要素提取 Schema
BUSINESS_ELEMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "institution_name": {"type": "string", "description": "报告机构名称"},
        "report_type": {"type": "string", "description": "报告类型"},
        "report_period": {"type": "string", "description": "报告期间"},
        "report_date": {"type": "string", "description": "报告日期"},
        "business_areas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "涉及的业务领域列表",
        },
        "key_metrics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "关键指标项",
        },
        "risk_indicators": {
            "type": "array",
            "items": {"type": "string"},
            "description": "风险指标项",
        },
    },
    "required": ["institution_name", "report_type", "report_period", "business_areas"],
}

# 审核范围判断 Schema
REVIEW_SCOPE_SCHEMA = {
    "type": "object",
    "properties": {
        "review_scope": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "area": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "focus_points": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "relevant_regulations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "notes": {"type": "string"},
    },
    "required": ["review_scope", "relevant_regulations"],
}


class DispatcherNode:
    """分发节点"""

    @staticmethod
    async def run(state: GraphState) -> dict[str, Any]:
        """执行分发阶段"""
        document_text = state.get("document_text", "")
        business_type = state.get("business_type")
        review_id = state.get("review_id")

        logger.info(f"[Dispatcher] Review {review_id}: 开始分发阶段")

        # 截断长文本（8K tokens 限制）
        truncated_text = document_text[:8000] if len(document_text) > 8000 else document_text

        # Step 1: 提取业务要素
        business_elements = await DispatcherNode._extract_elements(truncated_text, business_type)

        # Step 2: 确定审核范围
        scope_result = await DispatcherNode._determine_scope(truncated_text, business_elements)

        logger.info(
            f"[Dispatcher] Review {review_id}: "
            f"机构={business_elements.get('institution_name', 'N/A')}, "
            f"类型={business_elements.get('report_type', 'N/A')}, "
            f"范围={len(scope_result.get('review_scope', []))}项"
        )

        return {
            "business_elements": business_elements,
            "review_scope": scope_result.get("review_scope", []),
            "relevant_regulations": scope_result.get("relevant_regulations", []),
            "dispatcher_notes": scope_result.get("notes"),
            "stage_history": [f"[Dispatcher] 完成要素提取和范围确定"],
        }

    @staticmethod
    async def _extract_elements(
        text: str, business_type: Optional[str]
    ) -> dict:
        """提取业务要素"""
        prompt = (
            f"你是一个金融合规审核专家。请从以下报告开头部分提取关键业务要素。\n"
            f"报告类型提示: {business_type or '未知'}\n\n"
            f"报告内容:\n{text[:4000]}"
        )

        try:
            result = await llm_service.chat_structured(
                messages=[{"role": "user", "content": prompt}],
                output_schema=BUSINESS_ELEMENTS_SCHEMA,
            )
            return result
        except Exception as e:
            logger.error(f"Element extraction failed: {e}")
            return {
                "institution_name": "",
                "report_type": business_type or "unknown",
                "report_period": "",
                "report_date": "",
                "business_areas": [],
                "key_metrics": [],
                "risk_indicators": [],
            }

    @staticmethod
    async def _determine_scope(
        text: str, elements: dict
    ) -> dict:
        """确定审核范围"""
        elements_str = json.dumps(elements, ensure_ascii=False, indent=2)
        prompt = (
            f"基于以下报告的业务要素，确定该报告的合规审核范围。\n"
            f"需要考虑的审核领域包括但不限于：信息披露合规、风险管理、资本充足率、"
            f"关联交易、内部控制、数据治理、反洗钱等。\n\n"
            f"业务要素:\n{elements_str}\n\n"
            f"报告内容(部分):\n{text[:4000]}"
        )

        try:
            result = await llm_service.chat_structured(
                messages=[{"role": "user", "content": prompt}],
                output_schema=REVIEW_SCOPE_SCHEMA,
            )
            return result
        except Exception as e:
            logger.error(f"Scope determination failed: {e}")
            return {
                "review_scope": [],
                "relevant_regulations": [],
                "notes": f"范围自动确定失败: {e}",
            }
