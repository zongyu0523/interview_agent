"""
Resume parser。
流程：
  1. 接收 PDF bytes（來自前端上傳）
  2. 用 pymupdf 萃取純文字
  3. 送給 LLM（structured output via instructor）
  4. 存成 data/interview/resume.json
"""
import asyncio

import fitz  # pymupdf
from pydantic import BaseModel

from src.core.llm_client import get_async_instructor_client, get_model
from src.core.prompts.resume_parser import build_resume_parser_prompt
from src.db import resume_store


# ── Pydantic schema（對應前端 ResumeData）──────────────────────────────────────

class BasicInfo(BaseModel):
    name: str = ""
    location: str = ""
    languages: list[str] = []
    hard_skills: list[str] = []
    soft_skills: list[str] = []


class InterviewHook(BaseModel):
    topic_name: str = ""
    source_type: str = ""
    key_details: str = ""


class WorkExperience(BaseModel):
    company: str = ""
    role: str = ""
    date_range: str = ""
    responsibilities_and_achievements: str = ""


class Education(BaseModel):
    school: str = ""
    degree: str = ""
    major: str = ""
    graduation_year: str = ""


class ResumeData(BaseModel):
    basic_info: BasicInfo = BasicInfo()
    professional_summary: str = ""
    interview_hooks: list[InterviewHook] = []
    work_experience: list[WorkExperience] = []
    education: list[Education] = []


# ── PDF 萃取 ───────────────────────────────────────────────────────────────────

def _extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """用 pymupdf 從 bytes 萃取 PDF 純文字。"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


# ── 主函式 ─────────────────────────────────────────────────────────────────────

async def parse_resume_bytes(pdf_bytes: bytes) -> dict:
    """
    PDF bytes → 萃取文字 → LLM 解析 → 存 resume.json → 回傳結果。
    """
    raw_text = await asyncio.to_thread(_extract_text_from_bytes, pdf_bytes)

    print(f"\n[resume_parser] Parsing PDF ({len(raw_text)} chars)")

    system_prompt = build_resume_parser_prompt()
    client = get_async_instructor_client()

    result: ResumeData = await client.chat.completions.create(
        model=get_model("resume_parser"),
        max_tokens=8192,
        response_model=ResumeData,
        max_retries=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"<resume_text>\n{raw_text}\n</resume_text>\n\nParse this resume now.",
            },
        ],
    )

    data = result.model_dump()
    data["status"] = "parsed"

    await asyncio.to_thread(resume_store.save, data)
    print(f"[resume_parser] Done. Saved to resume.json")

    return data
