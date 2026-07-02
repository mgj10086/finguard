"""知识库管理 API"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.regulation import (
    Chapter, Clause, Regulation, RegulationSource, RegulationStatus, ViolationCase,
)
from backend.services.rag_engine import rag_engine

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/regulations/upload")
async def upload_regulation(
    file: UploadFile = File(...),
    source: RegulationSource = RegulationSource.CBIRC,
    title: Optional[str] = None,
    doc_number: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """上传法规文档并建立索引"""
    import uuid
    from pathlib import Path

    ext = Path(file.filename).suffix.lower()
    if ext not in {".pdf", ".docx"}:
        raise HTTPException(400, detail="仅支持 PDF/Word 文件")

    # 保存文件
    reg_dir = Path(__file__).parent.parent.parent.parent / "data" / "regulations" / source.value
    reg_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = reg_dir / unique_name

    content = await file.read()
    file_path.write_bytes(content)

    # 创建法规记录
    regulation = Regulation(
        title=title or file.filename,
        source=source,
        doc_number=doc_number,
        file_path=str(file_path),
        status=RegulationStatus.ACTIVE,
    )
    db.add(regulation)
    await db.commit()
    await db.refresh(regulation)

    # 异步触发索引构建
    try:
        index_result = await rag_engine.build_index([str(file_path)])
    except Exception as e:
        raise HTTPException(500, detail=f"索引构建失败: {e}")

    return {
        "code": 200,
        "message": "法规上传并索引成功",
        "data": {
            "id": regulation.id,
            "title": regulation.title,
            "source": source.value,
            "index_stats": index_result,
        },
    }


@router.get("/regulations")
async def list_regulations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[RegulationSource] = None,
    db: AsyncSession = Depends(get_db),
):
    """法规列表"""
    query = select(Regulation).order_by(Regulation.effective_date.desc().nullslast())
    if source:
        query = query.where(Regulation.source == source)

    total_result = await db.execute(select(Regulation))
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    regulations = result.scalars().all()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "short_title": r.short_title,
                    "source": r.source.value,
                    "doc_number": r.doc_number,
                    "status": r.status.value,
                    "publish_date": r.publish_date.isoformat() if r.publish_date else None,
                    "effective_date": r.effective_date.isoformat() if r.effective_date else None,
                }
                for r in regulations
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/search")
async def search_regulations(
    query: str,
    top_k: int = Query(5, ge=1, le=20),
):
    """语义检索法规条款"""
    results = await rag_engine.search(query, top_k=top_k)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": query,
            "results": results,
        },
    }
