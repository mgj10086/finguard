"""
文档模型

存储用户上传的待审核文档元数据。
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class DocumentStatus(str, enum.Enum):
    """文档状态"""
    UPLOADED = "uploaded"       # 已上传
    PARSING = "parsing"         # 解析中
    PARSED = "parsed"           # 解析完成
    FAILED = "failed"           # 解析失败


class DocumentType(str, enum.Enum):
    """文档类型"""
    DISCLOSURE_REPORT = "disclosure_report"   # 信息披露报告
    RISK_SELF_ASSESSMENT = "risk_self_assessment"  # 风险自评表
    ANNUAL_REPORT = "annual_report"           # 年报
    OTHER = "other"                           # 其他


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小(bytes)")
    file_type: Mapped[str] = mapped_column(String(10), nullable=False, comment="pdf/docx")
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"),
        default=DocumentType.OTHER,
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="解析后的纯文本")
    parsed_metadata: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),  # SQLite 兼容
        nullable=True,
        default=dict,
        comment="解析元数据（表格、章节等）",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关联
    reviews = relationship("Review", back_populates="document", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Document {self.id}: {self.original_filename}>"
