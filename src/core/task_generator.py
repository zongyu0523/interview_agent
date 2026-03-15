"""
init_task_generate_node
使用 instructor + LiteLLM 結構化輸出生成面試任務清單。
"""
from pydantic import BaseModel

from src.core.llm_client import get_instructor_client, get_async_instructor_client, get_model
from src.core.prompts.task_generator import build_task_generator_prompt
from src.logger import get_logger

log = get_logger("task_generator")


# ── Pydantic schema ────────────────────────────────────────────────────────────

class InterviewTask(BaseModel):
    topic: str
    instruction: str
    status: str = "pending"


class InterviewTaskList(BaseModel):
    tasks: list[InterviewTask]


# ── 主函式 ─────────────────────────────────────────────────────────────────────

def generate_tasks(
    interview_type: str,
    resume: dict,
    company_name: str,
    job_title: str,
    industry: str = "",
    job_description: str = "",
    additional_notes: str = "",
    must_ask_questions: list[str] | None = None,
    api_key: str | None = None,
) -> list[dict]:
    """
    呼叫 LLM，回傳結構化任務清單 list[dict]。
    失敗時回傳空 list，不擋 session 建立。
    """
    system_prompt = build_task_generator_prompt(
        interview_type=interview_type,
        resume=resume,
        company_name=company_name,
        job_title=job_title,
        industry=industry,
        job_description=job_description,
        additional_notes=additional_notes,
        must_ask_questions=must_ask_questions,
    )

    log.info("generating tasks", extra={"type": interview_type, "company": company_name, "blocks": len(system_prompt)})

    client = get_instructor_client()
    result: InterviewTaskList = client.chat.completions.create(
        model=get_model("task_generator"),
        max_tokens=8192,
        response_model=InterviewTaskList,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the interview task list now."},
        ],
        **({"api_key": api_key} if api_key else {}),
    )

    tasks = [task.model_dump() for task in result.tasks]
    log.info("tasks generated", extra={"count": len(tasks)})
    return tasks


async def generate_tasks_async(
    interview_type: str,
    resume: dict,
    company_name: str,
    job_title: str,
    industry: str = "",
    job_description: str = "",
    additional_notes: str = "",
    must_ask_questions: list[str] | None = None,
    api_key: str | None = None,
) -> list[dict]:
    """
    非同步版 generate_tasks，使用 AsyncInstructor。
    失敗時回傳空 list，不擋 session 建立。
    """
    system_prompt = build_task_generator_prompt(
        interview_type=interview_type,
        resume=resume,
        company_name=company_name,
        job_title=job_title,
        industry=industry,
        job_description=job_description,
        additional_notes=additional_notes,
        must_ask_questions=must_ask_questions,
    )

    log.info("generating tasks (async)", extra={"type": interview_type, "company": company_name})

    client = get_async_instructor_client()
    result: InterviewTaskList = await client.chat.completions.create(
        model=get_model("task_generator"),
        max_tokens=8192,
        response_model=InterviewTaskList,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the interview task list now."},
        ],
        **({"api_key": api_key} if api_key else {}),
    )

    tasks = [task.model_dump() for task in result.tasks]
    log.info("tasks generated", extra={"count": len(tasks)})
    return tasks
