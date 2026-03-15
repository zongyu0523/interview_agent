"""
履歷與職位描述匹配度分析。
使用 instructor + LiteLLM 產出結構化分析結果。
"""
from pydantic import BaseModel, Field

from src.core import llm_client
from src.core.llm_client import get_async_instructor_client


class MatchResult(BaseModel):
    score: int = Field(description="Match score from 1 to 10")
    label: str = Field(description="Short label: Strong Fit / Good Fit / Moderate Fit / Weak Fit")
    score_reason: str = Field(description="2-4 sentences explaining the match score")


_LABEL_MAP = {
    (8, 10): "Strong Fit",
    (6, 7):  "Good Fit",
    (4, 5):  "Moderate Fit",
    (1, 3):  "Weak Fit",
}


def _score_to_label(score: int) -> str:
    for (lo, hi), label in _LABEL_MAP.items():
        if lo <= score <= hi:
            return label
    return "Weak Fit"


def _format_resume(resume: dict) -> str:
    parts: list[str] = []

    basic = resume.get("basic_info", {})
    if name := basic.get("name"):
        parts.append(f"Name: {name}")
    if loc := basic.get("location"):
        parts.append(f"Location: {loc}")
    if langs := basic.get("languages"):
        parts.append(f"Languages: {', '.join(langs)}")
    if hard := basic.get("hard_skills"):
        parts.append(f"Hard Skills: {', '.join(hard)}")
    if soft := basic.get("soft_skills"):
        parts.append(f"Soft Skills: {', '.join(soft)}")

    if summary := resume.get("professional_summary"):
        parts.append(f"\nProfessional Summary:\n{summary}")

    work_exps = resume.get("work_experience", [])
    if work_exps:
        parts.append("\nWork Experience:")
        for exp in work_exps:
            line = f"  - {exp.get('role', '')} at {exp.get('company', '')}"
            if dr := exp.get("date_range"):
                line += f" ({dr})"
            parts.append(line)
            if resp := exp.get("responsibilities_and_achievements"):
                parts.append(f"    {resp}")

    edu = resume.get("education", [])
    if edu:
        parts.append("\nEducation:")
        for e in edu:
            line = f"  - {e.get('degree', '')} in {e.get('major', '')} from {e.get('school', '')}"
            if yr := e.get("graduation_year"):
                line += f" ({yr})"
            parts.append(line)

    hooks = resume.get("interview_hooks", [])
    if hooks:
        parts.append("\nKey Highlights:")
        for h in hooks:
            parts.append(f"  - {h.get('topic_name', '')}: {h.get('key_details', '')}")

    return "\n".join(parts)


def analyze(resume: dict, company: dict) -> MatchResult:
    """
    Compare resume against job description and return a MatchResult.
    Raises on LLM error.
    """
    resume_text = _format_resume(resume)
    job_title = company.get("job_title", "")
    company_name = company.get("company_name", "")
    job_desc = company.get("job_description", "")
    industry = company.get("industry", "")

    system_prompt = (
        "You are a senior talent acquisition specialist. "
        "Evaluate how well a candidate's resume matches a job opening. "
        "Be objective and concise."
    )

    user_prompt = f"""## Job Opening
Company: {company_name}
Title: {job_title}
Industry: {industry}
Description:
{job_desc or '(No description provided)'}

## Candidate Resume
{resume_text or '(No resume data)'}

Analyze the match and return:
- score: integer 1–10 (10 = perfect match)
- label: one of "Strong Fit" / "Good Fit" / "Moderate Fit" / "Weak Fit"
- score_reason: 2–4 sentences covering key matching strengths and gaps"""

    client = llm_client.get_instructor_client()
    result: MatchResult = client.chat.completions.create(
        model=llm_client.get_model("match_analyzer"),
        response_model=MatchResult,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=8192,
    )

    # Enforce label consistency with score
    result.label = _score_to_label(result.score)
    return result


async def analyze_async(resume: dict, company: dict) -> MatchResult:
    """
    非同步版 analyze，使用 AsyncInstructor。
    """
    resume_text = _format_resume(resume)
    job_title = company.get("job_title", "")
    company_name = company.get("company_name", "")
    job_desc = company.get("job_description", "")
    industry = company.get("industry", "")

    system_prompt = (
        "You are a senior talent acquisition specialist. "
        "Evaluate how well a candidate's resume matches a job opening. "
        "Be objective and concise."
    )

    user_prompt = f"""## Job Opening
Company: {company_name}
Title: {job_title}
Industry: {industry}
Description:
{job_desc or '(No description provided)'}

## Candidate Resume
{resume_text or '(No resume data)'}

Analyze the match and return:
- score: integer 1–10 (10 = perfect match)
- label: one of "Strong Fit" / "Good Fit" / "Moderate Fit" / "Weak Fit"
- score_reason: 2–4 sentences covering key matching strengths and gaps"""

    client = get_async_instructor_client()
    result: MatchResult = await client.chat.completions.create(
        model=llm_client.get_model("match_analyzer"),
        response_model=MatchResult,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=8192,
    )

    result.label = _score_to_label(result.score)
    return result
