"""
阶段 3: 裁决 (Adjudicator)

职责：
1. 查询知识图谱，为每项发现匹配历史违规案例
2. 基于案例相似度评估风险程度
3. 综合 RAG 检索结果和图谱证据，生成裁决意见
4. 合并/去重问题，消除误报

输入: reviewer_findings, business_elements
输出: case_matches, graph_evidence, adjudicator_findings
"""

import logging
from typing import Any

from backend.agents.graph import GraphState
from backend.services.knowledge_graph import knowledge_graph
from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AdjudicatorNode:
    """裁决节点"""

    @staticmethod
    async def run(state: GraphState) -> dict[str, Any]:
        """执行裁决阶段"""
        findings = state.get("reviewer_findings", [])
        business_elements = state.get("business_elements", {})
        review_id = state.get("review_id")

        logger.info(
            f"[Adjudicator] Review {review_id}: 开始裁决阶段, "
            f"待裁决发现={len(findings)}项"
        )

        if not findings:
            logger.info(f"[Adjudicator] Review {review_id}: 无发现，跳过")
            return {
                "case_matches": [],
                "graph_evidence": [],
                "adjudicator_findings": [],
                "stage_history": ["[Adjudicator] 无发现，跳过"],
            }

        # 逐项查询知识图谱，获取历史案例证据
        all_case_matches = []
        for finding in findings:
            cases = await AdjudicatorNode._match_cases(finding)
            all_case_matches.extend(cases)

        # 综合裁决：结合 RAG 证据和图谱证据，生成最终判定
        adjudicated = await AdjudicatorNode._adjudicate_findings(
            findings, all_case_matches, business_elements
        )

        logger.info(
            f"[Adjudicator] Review {review_id}: "
            f"裁决完成, {len(adjudicated)}项判定"
        )

        return {
            "case_matches": all_case_matches,
            "graph_evidence": all_case_matches,
            "adjudicator_findings": adjudicated,
            "stage_history": [
                f"[Adjudicator] 完成 {len(findings)} 项裁决, "
                f"匹配 {len(all_case_matches)} 个历史案例"
            ],
        }

    @staticmethod
    async def _match_cases(finding: dict) -> list[dict]:
        """为单个发现匹配知识图谱中的违规案例"""
        description = finding.get("description", "")
        title = finding.get("title", "")

        try:
            cases = await knowledge_graph.search_similar_cases(
                f"{title} {description}", limit=3
            )
            return [
                {
                    "finding_title": title,
                    "case_title": c.get("title", ""),
                    "case_description": c.get("description", ""),
                    "penalty": c.get("penalty", ""),
                    "institution": c.get("institution", ""),
                    "similarity_score": c.get("score", 0.0),
                }
                for c in cases
                if c.get("score", 0) > 0.5
            ]
        except Exception as e:
            logger.warning(f"Case matching failed for '{title}': {e}")
            return []

    @staticmethod
    async def _adjudicate_findings(
        findings: list[dict],
        case_matches: list[dict],
        business_elements: dict,
    ) -> list[dict]:
        """综合裁决：去伪存真、风险评级"""
        if len(findings) <= 2:
            # 发现很少时直接返回（LLM 调用成本 > 收益）
            for f in findings:
                f["reasoning"] = "基于法规条款直接比对"
                f["confirmed"] = True
            return findings

        # 构建裁决上下文
        case_evidence = "\n".join([
            f"- {c['finding_title']}: 历史案例「{c['case_title']}」"
            f"处罚: {c.get('penalty', '未知')}"
            for c in case_matches[:10]
        ]) if case_matches else "无匹配历史案例"

        findings_summary = "\n".join([
            f"{i+1}. [{f['severity']}] {f['title']}: {f['description'][:200]}"
            for i, f in enumerate(findings)
        ])

        prompt = (
            "你是一个资深金融合规审核官。请对以下审核发现进行最终裁决。\n\n"
            f"=== 审核发现 ===\n{findings_summary}\n\n"
            f"=== 历史案例证据 ===\n{case_evidence}\n\n"
            "请执行以下裁决：\n"
            "1. 确认误报(confirmed=false): 如果该发现不构成实质性违规\n"
            "2. 调整风险等级: 根据历史案例处罚力度调整 severity\n"
            "3. 补充推理过程: 说明为什么构成/不构成违规\n"
            "4. 标记需要人工复审(needs_human=True): 如果是重大复杂事项\n\n"
            "对每项发现，返回裁决意见。"
        )

        ADJUDICATION_SCHEMA = {
            "type": "object",
            "properties": {
                "adjudications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer"},
                            "confirmed": {"type": "boolean"},
                            "adjusted_severity": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low", "info"],
                            },
                            "reasoning": {"type": "string"},
                            "needs_human_review": {"type": "boolean"},
                            "suggestion": {"type": "string"},
                        },
                        "required": ["index", "confirmed", "adjusted_severity", "reasoning"],
                    },
                }
            },
            "required": ["adjudications"],
        }

        try:
            result = await llm_service.chat_structured(
                messages=[{"role": "user", "content": prompt}],
                output_schema=ADJUDICATION_SCHEMA,
            )
            adjudications = result.get("adjudications", [])

            # 合并裁决意见到发现中
            adjudication_map = {
                a["index"]: a for a in adjudications if "index" in a
            }
            adjudicated = []
            for i, f in enumerate(findings):
                adj = adjudication_map.get(i + 1, {})
                if adj.get("confirmed", True):
                    f["severity"] = adj.get("adjusted_severity", f.get("severity", "medium"))
                    f["reasoning"] = adj.get("reasoning", f.get("reasoning", ""))
                    f["suggestion"] = adj.get("suggestion", f.get("suggestion", ""))
                    adjudicated.append(f)
                else:
                    logger.info(f"Adjudicator 排除了误报: {f['title']}")

            return adjudicated

        except Exception as e:
            logger.error(f"Adjudication failed, using raw findings: {e}")
            for f in findings:
                f["reasoning"] = "裁决阶段异常，保留审核阶段判定"
            return findings
