"""
审核模型

存储审核流水线的状态和结果。
对应 LangGraph State 的持久化层。
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class ReviewStatus(str, enum.Enum):
    """审核状态"""
    PENDING = "pending"              # 待处理
    DISPATCHING = "dispatching"      # 分发中 (Stage 1)
    REVIEWING = "reviewing"          # 审核中 (Stage 2)
    ADJUDICATING = "adjudicating"    # 裁决中 (Stage 3)
    FINAL_REVIEWING = "final_reviewing"  # 复审中 (Stage 4)
    COMPLETED = "completed"          # 已完成
    REJECTED = "rejected"            # 退回人工
    FAILED = "failed"                # 系统失败


class FindingSeverity(str, enum.Enum):
    """发现问题严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Review(Base):
    """审核任务主表"""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid4()),
        comment="对外暴露的唯一标识"
    )
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="审核任务名称")
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"),
        default=ReviewStatus.PENDING,
        nullable=False,
    )
    business_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="业务类型（如 信息披露、风险自评）"
    )

    # 审核结果
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核结论摘要")
    total_findings: Mapped[int] = mapped_column(Integer, default=0, comment="发现问题总数")
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    low_count: Mapped[int] = mapped_column(Integer, default=0)
    compliance_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="合规评分 0-100"
    )

    # Agent 状态
    current_stage: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="当前流水线阶段"
    )
    agent_state: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),
        nullable=True, default=dict,
        comment="LangGraph Agent 完整状态快照",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="失败原因")

    # 人工复审
    needs_human_review: Mapped[bool] = mapped_column(
        default=False, comment="是否需要人工介入"
    )
    human_reviewer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    human_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关联
    document = relationship("Document", back_populates="reviews", lazy="selectin")
    findings = relationship("Finding", back_populates="review", lazy="selectin",
                           cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Review {self.uuid}: {self.title} [{self.status.value}]>"


class Finding(Base):
    """审核发现的具体问题"""
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    clause_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clauses.id", ondelete="SET NULL"), nullable=True,
        comment="关联法规条款"
    )

    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity"),
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="问题分类"
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="问题简述")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="详细描述")

    # 原文位置
    source_section: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="原文章节"
    )
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="原文引用")

    # 法规引用
    regulation_cited: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="引用的法规条款名"
    )
    regulation_text: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="法规原文引用"
    )
    citation_rank: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="RAG 检索排名"
    )
    citation_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="相似度分数"
    )

    # 推理过程
    reasoning: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="AI 推理过程（可解释性）"
    )
    graph_evidence: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),
        nullable=True, default=dict,
        comment="知识图谱证据（相关案例）",
    )
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True, comment="整改建议")

    # 人工确认
    confirmed: Mapped[bool | None] = mapped_column(default=None, comment="人工确认结果")
    human_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Agent
    source_agent: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="发现该问题的 Agent"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联
    review = relationship("Review", back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding {self.id}: [{self.severity.value}] {self.title}>"
