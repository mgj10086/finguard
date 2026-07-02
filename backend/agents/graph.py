"""
LangGraph 状态图定义

四阶段 Agent 流水线：
1. Dispatcher  （分发）  — 提取业务要素，确定审核范围
2. Reviewer    （审核）  — RAG 检索法规 + LLM 逐条比对
3. Adjudicator （裁决）  — 知识图谱推理 + 综合判定
4. FinalReview（复审）  — 结论汇总、可解释性生成

图结构：
  START → Dispatcher → Reviewer → Adjudicator → FinalReview → END
                │            │             │
                └──→ 条件分支：若不需要某阶段则跳过
"""

import logging
import operator
from typing import Annotated, Any, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from backend.agents.dispatcher import DispatcherNode
from backend.agents.reviewer import ReviewerNode
from backend.agents.adjudicator import AdjudicatorNode
from backend.agents.final_reviewer import FinalReviewNode

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """LangGraph 全局状态"""

    # 任务标识
    review_id: int                         # 审核任务 ID (PostgreSQL)
    document_id: int                       # 文档 ID
    document_text: str                     # 文档全文
    business_type: Optional[str]           # 业务类型

    # 阶段 1: 分发 (Dispatcher)
    business_elements: dict                # 提取的业务要素 {key: value}
    review_scope: list[str]                # 审核范围列表
    relevant_regulations: list[str]        # 相关法规列表
    dispatcher_notes: Optional[str]        # 分发备注

    # 阶段 2: 审核 (Reviewer)
    clause_matches: list[dict]             # 条款匹配结果
    retrieved_chunks: list[dict]           # RAG 检索到的原文块
    reviewer_findings: list[dict]          # 审核发现的问题

    # 阶段 3: 裁决 (Adjudicator)
    case_matches: list[dict]               # 匹配的违规案例
    graph_evidence: list[dict]             # 知识图谱证据
    adjudicator_findings: list[dict]       # 裁决后的问题列表（合并/去重）

    # 阶段 4: 复审 (FinalReview)
    conclusions: list[dict]                # 最终结论
    summary: str                           # 审核摘要
    compliance_score: float                # 合规评分
    needs_human_review: bool               # 是否需要人工介入
    human_review_reason: Optional[str]     # 人工介入原因

    # 运行时
    errors: Annotated[list[str], operator.add]  # 错误列表
    stage_history: Annotated[list[str], operator.add]  # 阶段日志


def create_review_graph() -> StateGraph:
    """
    创建审核流水线状态图
    """
    workflow = StateGraph(GraphState)

    # 注册节点
    workflow.add_node("dispatcher", DispatcherNode.run)
    workflow.add_node("reviewer", ReviewerNode.run)
    workflow.add_node("adjudicator", AdjudicatorNode.run)
    workflow.add_node("final_review", FinalReviewNode.run)

    # 连接：分发 → 审核 → 裁决 → 复审
    workflow.set_entry_point("dispatcher")
    workflow.add_edge("dispatcher", "reviewer")

    # 裁决后检查是否需要跳过（无发现时直接到结束）
    workflow.add_conditional_edges(
        "reviewer",
        _route_after_review,
        {"adjudicator": "adjudicator", "final_review": "final_review"},
    )

    workflow.add_edge("adjudicator", "final_review")
    workflow.add_edge("final_review", END)

    # 编译（启用内存 Checkpoint 支持 HITL 人工介入）
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app


def _route_after_review(state: GraphState) -> str:
    """
    审核后的路由决策：
    - 有发现 → 进入裁决阶段
    - 无发现 → 直接进入复审
    """
    if state.get("reviewer_findings") and len(state["reviewer_findings"]) > 0:
        return "adjudicator"
    return "final_review"


# 全局 Graph 实例
review_graph = create_review_graph()


async def run_review_pipeline(
    review_id: int,
    document_id: int,
    document_text: str,
    business_type: Optional[str] = None,
) -> dict[str, Any]:
    """
    执行完整审核流水线

    Args:
        review_id: 审核任务 ID
        document_id: 文档 ID
        document_text: 文档全文
        business_type: 业务类型

    Returns:
        最终状态 dict
    """
    initial_state: GraphState = {
        "review_id": review_id,
        "document_id": document_id,
        "document_text": document_text,
        "business_type": business_type,
        # 阶段 1
        "business_elements": {},
        "review_scope": [],
        "relevant_regulations": [],
        "dispatcher_notes": None,
        # 阶段 2
        "clause_matches": [],
        "retrieved_chunks": [],
        "reviewer_findings": [],
        # 阶段 3
        "case_matches": [],
        "graph_evidence": [],
        "adjudicator_findings": [],
        # 阶段 4
        "conclusions": [],
        "summary": "",
        "compliance_score": 0.0,
        "needs_human_review": False,
        "human_review_reason": None,
        # 运行时
        "errors": [],
        "stage_history": [],
    }

    config = {"configurable": {"thread_id": f"review_{review_id}"}}

    try:
        final_state = await review_graph.ainvoke(initial_state, config)
        logger.info(
            f"Review {review_id} completed: "
            f"{len(final_state.get('conclusions', []))} conclusions, "
            f"score={final_state.get('compliance_score', 0):.1f}"
        )
        return final_state
    except Exception as e:
        logger.error(f"Review pipeline failed for {review_id}: {e}", exc_info=True)
        return {
            **initial_state,
            "errors": [str(e)],
            "summary": f"审核流水线异常终止: {str(e)}",
            "compliance_score": 0.0,
        }
