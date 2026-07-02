"""审核流水线 API"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.graph import run_review_pipeline
from backend.core.database import get_db
from backend.models.review import Finding, FindingSeverity, Review, ReviewStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("")
async def create_review(
    document_id: int,
    title: Optional[str] = None,
    business_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """创建审核任务"""
    from backend.models.document import Document

    # 确认文档存在且已解析
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, detail="文档不存在")
    if doc.status.value != "parsed":
        raise HTTPException(400, detail="文档尚未解析完成，请等待解析")

    # 创建审核记录
    review = Review(
        document_id=document_id,
        title=title or f"审核: {doc.original_filename}",
        business_type=business_type,
        status=ReviewStatus.PENDING,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return {
        "code": 200,
        "message": "审核任务已创建",
        "data": {
            "id": review.id,
            "uuid": review.uuid,
            "title": review.title,
            "status": review.status.value,
        },
    }


@router.post("/{review_id}/start")
async def start_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    """启动审核流水线"""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, detail="审核任务不存在")

    # 更新状态为分发中
    await db.execute(
        update(Review)
        .where(Review.id == review_id)
        .values(status=ReviewStatus.DISPATCHING)
    )
    await db.commit()

    # 获取文档文本
    from backend.models.document import Document
    doc_result = await db.execute(select(Document).where(Document.id == review.document_id))
    doc = doc_result.scalar_one()

    # 异步执行流水线（实际生产环境应使用 Celery 后台任务）
    try:
        final_state = await run_review_pipeline(
            review_id=review_id,
            document_id=review.document_id,
            document_text=doc.parsed_text or "",
            business_type=review.business_type,
        )

        # 持久化审核结果
        new_status = (
            ReviewStatus.REJECTED
            if final_state.get("needs_human_review")
            else ReviewStatus.COMPLETED
        )

        # 保存发现
        for conclusion in final_state.get("conclusions", []):
            finding = Finding(
                review_id=review_id,
                severity=FindingSeverity(conclusion.get("severity", "medium")),
                title=conclusion.get("title", ""),
                description=conclusion.get("description", ""),
                source_text=conclusion.get("source_text"),
                regulation_cited=conclusion.get("regulation_cited"),
                reasoning=conclusion.get("reasoning"),
                suggestion=conclusion.get("suggestion"),
                source_agent="adjudicator",
            )
            db.add(finding)

        # 更新审核任务
        await db.execute(
            update(Review)
            .where(Review.id == review_id)
            .values(
                status=new_status,
                summary=final_state.get("summary"),
                compliance_score=final_state.get("compliance_score", 0.0),
                total_findings=len(final_state.get("conclusions", [])),
                critical_count=sum(
                    1 for c in final_state.get("conclusions", [])
                    if c.get("severity") == "critical"
                ),
                high_count=sum(
                    1 for c in final_state.get("conclusions", [])
                    if c.get("severity") == "high"
                ),
                medium_count=sum(
                    1 for c in final_state.get("conclusions", [])
                    if c.get("severity") == "medium"
                ),
                low_count=sum(
                    1 for c in final_state.get("conclusions", [])
                    if c.get("severity") == "low"
                ),
                needs_human_review=final_state.get("needs_human_review", False),
                human_review_reason=final_state.get("human_review_reason"),
                agent_state=final_state,
                completed_at=__import__("datetime").datetime.utcnow(),
            )
        )
        await db.commit()

    except Exception as e:
        logger.error(f"Review pipeline failed: {e}", exc_info=True)
        await db.execute(
            update(Review)
            .where(Review.id == review_id)
            .values(status=ReviewStatus.FAILED, error_message=str(e))
        )
        await db.commit()
        raise HTTPException(500, detail=f"审核流水线执行失败: {str(e)}")

    return {
        "code": 200,
        "message": "审核完成",
        "data": {
            "id": review_id,
            "status": new_status.value,
            "compliance_score": final_state.get("compliance_score", 0.0),
            "total_findings": len(final_state.get("conclusions", [])),
            "summary": final_state.get("summary"),
            "needs_human_review": final_state.get("needs_human_review", False),
        },
    }


@router.get("")
async def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ReviewStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """审核任务列表"""
    query = select(Review).order_by(Review.created_at.desc())
    if status:
        query = query.where(Review.status == status)

    total_result = await db.execute(select(Review))
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    reviews = result.scalars().all()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": r.id,
                    "uuid": r.uuid,
                    "title": r.title,
                    "document_id": r.document_id,
                    "status": r.status.value,
                    "compliance_score": r.compliance_score,
                    "total_findings": r.total_findings,
                    "needs_human_review": r.needs_human_review,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in reviews
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{review_id}")
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    """审核详情"""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, detail="审核任务不存在")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": review.id,
            "uuid": review.uuid,
            "title": review.title,
            "document_id": review.document_id,
            "status": review.status.value,
            "summary": review.summary,
            "compliance_score": review.compliance_score,
            "total_findings": review.total_findings,
            "critical_count": review.critical_count,
            "high_count": review.high_count,
            "medium_count": review.medium_count,
            "low_count": review.low_count,
            "needs_human_review": review.needs_human_review,
            "human_review_reason": review.human_review_reason,
            "findings": [
                {
                    "id": f.id,
                    "severity": f.severity.value,
                    "title": f.title,
                    "description": f.description,
                    "source_section": f.source_section,
                    "regulation_cited": f.regulation_cited,
                    "reasoning": f.reasoning,
                    "suggestion": f.suggestion,
                }
                for f in (review.findings or [])
            ],
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "completed_at": review.completed_at.isoformat() if review.completed_at else None,
        },
    }


@router.post("/{review_id}/confirm")
async def confirm_review(
    review_id: int,
    action: str,  # "approve" or "reject"
    comment: Optional[str] = None,
    reviewer: str = "human",
    db: AsyncSession = Depends(get_db),
):
    """人工确认审核结果（HITL）"""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, detail="审核任务不存在")

    new_status = ReviewStatus.COMPLETED if action == "approve" else ReviewStatus.REJECTED

    await db.execute(
        update(Review)
        .where(Review.id == review_id)
        .values(
            status=new_status,
            human_reviewer=reviewer,
            human_comment=comment,
        )
    )
    await db.commit()

    return {
        "code": 200,
        "message": f"审核任务已{'通过' if action == 'approve' else '驳回'}",
        "data": {"id": review_id, "status": new_status.value},
    }
