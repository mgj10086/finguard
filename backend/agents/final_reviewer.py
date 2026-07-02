"""
阶段 4: 复审 (Final Review)

职责：
1. 汇总所有审核发现，生成结构化审核报告
2. 计算合规评分
3. 生成可解释性说明
4. 标记需要人工复核的复杂问题

输入: adjudicator_findings, case_matches, business_elements
输出: conclusions, summary, compliance_score, needs_human_review
"""

import logging
from typing import Any

from backend.agents.graph import GraphState
from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class FinalReviewNode:
    """复审节点"""

    @staticmethod
    async def run(state: GraphState) -> dict[str, Any]:
        """执行复审阶段"""
        findings = state.get("adjudicator_findings", [])
        business_elements = state.get("business_elements", {})
        review_id = state.get("review_id")

        logger.info(
            f"[FinalReview] Review {review_id}: 开始复审阶段, "
            f"待汇总发现={len(findings)}项"
        )

        # 计算严重程度分布
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.get("severity", "medium")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # 判断是否需要人工介入
        needs_human = False
        human_reason = None

        if severity_counts.get("critical", 0) > 0:
            needs_human = True
            human_reason = f"包含 {severity_counts['critical']} 项重大违规，需人工确认"

        has_critical_needs_review = any(
            f.get("needs_human_review", False) or f.get("severity") == "critical"
            for f in findings
        )
        if has_critical_needs_review:
            needs_human = True
            human_reason = human_reason or "裁决阶段标记需人工复审"

        # 计算合规评分
        score = FinalReviewNode._calculate_score(findings, severity_counts)

        # 生成审核结论摘要
        if findings:
            summary = await FinalReviewNode._generate_summary(
                findings, business_elements, score
            )
        else:
            summary = f"经审核，未发现合规问题。合规评分: {score:.1f}/100。"

        # 构建结构化结论
        conclusions = []
        for i, f in enumerate(findings):
            conclusions.append({
                "id": i + 1,
                "title": f.get("title", ""),
                "severity": f.get("severity", "medium"),
                "description": f.get("description", ""),
                "regulation_cited": f.get("regulation_cited", ""),
                "clause_num": f.get("clause_num", ""),
                "source_text": f.get("source_text", ""),
                "reasoning": f.get("reasoning", ""),
                "suggestion": f.get("suggestion", ""),
                "graph_cases": [
                    c for c in state.get("case_matches", [])
                    if c.get("finding_title") == f.get("title")
                ],
            })

        logger.info(
            f"[FinalReview] Review {review_id}: "
            f"评分={score:.1f}, "
            f"结论={len(conclusions)}项, "
            f"需人工={'是' if needs_human else '否'}"
        )

        return {
            "conclusions": conclusions,
            "summary": summary,
            "compliance_score": score,
            "needs_human_review": needs_human,
            "human_review_reason": human_reason,
            "stage_history": [
                f"[FinalReview] 评分 {score:.1f}, "
                f"{len(conclusions)}项结论"
            ],
        }

    @staticmethod
    def _calculate_score(
        findings: list[dict],
        severity_counts: dict[str, int],
    ) -> float:
        """计算合规评分 (0-100)"""
        if not findings:
            return 100.0

        # 权重: critical=40, high=20, medium=10, low=5, info=1
        weights = {"critical": 40, "high": 20, "medium": 10, "low": 5, "info": 1}
        total_deduction = sum(
            count * weights.get(sev, 0)
            for sev, count in severity_counts.items()
        )

        # 每个 high+ 问题额外扣 5 分复杂罚
        high_plus = severity_counts.get("critical", 0) + severity_counts.get("high", 0)
        total_deduction += high_plus * 5

        score = max(0, min(100, 100 - total_deduction))
        return round(score, 1)

    @staticmethod
    async def _generate_summary(
        findings: list[dict],
        business_elements: dict,
        score: float,
    ) -> str:
        """生成审核结论摘要"""
        findings_text = "\n".join([
            f"- [{f.get('severity', 'medium').upper()}] {f.get('title', '')}"
            for f in findings[:10]
        ])
        extra = f"\n...及其他 {len(findings) - 10} 项发现" if len(findings) > 10 else ""

        prompt = (
            "你是一个金融合规审核专家。请根据以下审核结果生成简明的审核摘要。\n\n"
            f"机构: {business_elements.get('institution_name', '未知')}\n"
            f"报告类型: {business_elements.get('report_type', '未知')}\n"
            f"期间: {business_elements.get('report_period', '未知')}\n"
            f"合规评分: {score}/100\n\n"
            f"审核发现:\n{findings_text}{extra}\n\n"
            "请输出 3-5 句话的审核摘要，包含：整体评价、主要发现、风险提示。"
        )

        try:
            content, _ = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            return content
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return (
                f"审核完成。合规评分: {score}/100。"
                f"共发现 {len(findings)} 项问题。"
                f"请查看详细结论了解具体情况。"
            )
