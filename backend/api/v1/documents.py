"""文档管理 API"""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.document import Document, DocumentStatus, DocumentType
from backend.services.document_parser import DocumentParser, parse_document_task

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "data" / "uploads"


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: DocumentType = DocumentType.OTHER,
    uploaded_by: str = "user",
    db: AsyncSession = Depends(get_db),
):
    """上传待审核文档"""
    # 校验文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in {".pdf", ".docx", ".doc"}:
        raise HTTPException(400, detail=f"不支持的文件类型: {ext}，仅支持 PDF/Word")

    # 保存文件
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_name

    content = await file.read()
    file_path.write_bytes(content)

    # 创建文档记录
    doc = Document(
        filename=unique_name,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=ext.lstrip("."),
        doc_type=doc_type,
        status=DocumentStatus.UPLOADED,
        uploaded_by=uploaded_by,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # 异步触发解析
    parse_document_task.delay(str(file_path))

    return {
        "code": 200,
        "message": "上传成功，正在解析",
        "data": {
            "id": doc.id,
            "filename": doc.original_filename,
            "status": doc.status.value,
        },
    }


@router.get("")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """文档列表"""
    query = select(Document).order_by(Document.created_at.desc())
    if status:
        query = query.where(Document.status == status)

    # 分页
    total = len((await db.execute(select(Document))).scalars().all())
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    docs = result.scalars().all()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": d.id,
                    "filename": d.original_filename,
                    "file_type": d.file_type,
                    "doc_type": d.doc_type.value,
                    "status": d.status.value,
                    "page_count": d.page_count,
                    "file_size": d.file_size,
                    "uploaded_by": d.uploaded_by,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in docs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """文档详情"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, detail="文档不存在")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": doc.id,
            "filename": doc.original_filename,
            "file_type": doc.file_type,
            "doc_type": doc.doc_type.value,
            "status": doc.status.value,
            "page_count": doc.page_count,
            "file_size": doc.file_size,
            "parsed_text": doc.parsed_text[:5000] if doc.parsed_text else None,
            "uploaded_by": doc.uploaded_by,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        },
    }
