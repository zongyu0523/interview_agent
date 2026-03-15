from fastapi import APIRouter, HTTPException, UploadFile, File

from src.core.resume_parser import parse_resume_bytes
from src.db import resume_store

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.get("")
def get_resume():
    """GET /api/resume — 取得目前履歷資料"""
    return resume_store.load()


@router.put("")
def update_resume(data: dict):
    """PUT /api/resume — 部分更新履歷"""
    return resume_store.update(data)


@router.post("/parse")
async def trigger_parse(file: UploadFile = File(...)):
    """
    POST /api/resume/parse — 接收 PDF，解析後回傳結構化履歷。
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        pdf_bytes = await file.read()
        return await parse_resume_bytes(pdf_bytes)
    except HTTPException:
        raise
    except Exception as e:
        from src.core.llm_client import check_auth_error
        check_auth_error(e)
        raise HTTPException(status_code=500, detail=str(e))
