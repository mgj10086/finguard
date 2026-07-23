"""
法规模型

存储金融监管法规的层级结构：法规 → 章节 → 条款 → 细则。
对应 LlamaIndex 的三级层级索引。
"""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class RegulationSource(str, enum.Enum):
    """法规来源"""
    CBIRC = "cbirc"         # 国家金融监督管理总局
    PBOC = "pboc"           # 中国人民银行
    CSRC = "csrc"           # 中国证监会
    OTHER = "other"         # 其他


class RegulationStatus(str, enum.Enum):
    """法规状态"""
    ACTIVE = "active"           # 现行有效
    AMENDED = "amended"         # 已被修订
    REPEALED = "repealed"       # 已被废止
    DRAFT = "draft"             # 征求意见稿


class Regulation(Base):
    """法规主表"""
    __tablename__ = "regulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="法规全称")
    short_title: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="简称")
    source: Mapped[RegulationSource] = mapped_column(
        Enum(RegulationSource, name="regulation_source"),
        nullable=False,
    )
    doc_number: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="文号")
    status: Mapped[RegulationStatus] = mapped_column(
        Enum(RegulationStatus, name="regulation_status"),
        default=RegulationStatus.ACTIVE,
        nullable=False,
    )
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="发布日期")
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="生效日期")
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="PDF/Word 源文件路径")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="法规摘要")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关联
    chapters = relationship("Chapter", back_populates="regulation", lazy="selectin",
                            order_by="Chapter.order_num")

    def __repr__(self) -> str:
        return f"<Regulation {self.id}: {self.short_title or self.title}>"


class Chapter(Base):
    """法规章节"""
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False, comment="章节序号")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联
    regulation = relationship("Regulation", back_populates="chapters")
    clauses = relationship("Clause", back_populates="chapter", lazy="selectin",
                           order_by="Clause.order_num")

    def __repr__(self) -> str:
        return f"<Chapter {self.order_num}: {self.title}>"


class Clause(Base):
    """法规条款 - 最小可检索单元"""
    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="条款原文")
    order_num: Mapped[str] = mapped_column(String(20), nullable=False, comment="条款编号（如 第X条）")
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True, comment="关键词（逗号分隔）")
    risk_level: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="风险等级: high/medium/low"
    )
    milvus_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Milvus 向量 ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联
    chapter = relationship("Chapter", back_populates="clauses")

    def __repr__(self) -> str:
        return f"<Clause {self.order_num}>"


class ViolationCase(Base):
    """违规案例 - 用于知识图谱推理"""
    __tablename__ = "violation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clause_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clauses.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="案例标题")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="违规事实描述")
    penalty: Mapped[str | None] = mapped_column(Text, nullable=True, comment="处罚结果")
    penalty_amount: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="处罚金额")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="处罚年份")
    institution_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="被处罚机构")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ViolationCase {self.id}: {self.title}>"
