"""
答案評分 prompt 組裝。
根據面試類型給出不同的評分重點。
"""

_TYPE_CRITERIA: dict[str, str] = {
    "recruiter": (
        "Evaluate based on clarity of communication, genuine motivation, and cultural fit signals. "
        "Look for specific examples and authentic enthusiasm."
    ),
    "technical": (
        "Evaluate based on technical accuracy, depth of reasoning, awareness of tradeoffs, "
        "and ability to explain complex concepts clearly."
    ),
    "behavioral": (
        "Evaluate based on STAR structure completeness (Situation, Task, Action, Result), "
        "specificity of examples, and measurable outcomes."
    ),
    "hiring_manager": (
        "Evaluate based on strategic thinking, leadership presence, long-term vision, "
        "and ability to connect individual work to business impact."
    ),
}


def build_score_prompt(
    interview_type: str,
    question: str,
    answer: str,
    task_topic: str = "",
    task_instruction: str = "",
) -> str:
    criteria = _TYPE_CRITERIA.get(interview_type, _TYPE_CRITERIA["recruiter"])

    context_lines = []
    if task_topic:
        context_lines.append(f"Topic being assessed: {task_topic}")
    if task_instruction:
        context_lines.append(f"What a good answer should cover: {task_instruction}")
    context_block = "\n".join(context_lines)

    return f"""You are an expert interview coach evaluating a candidate's answer.

## Interview Type
{interview_type.replace("_", " ").title()}

## Scoring Criteria
{criteria}

{f"## Task Context{chr(10)}{context_block}{chr(10)}" if context_block else ""}
## Interview Question
{question or "(no question recorded)"}

## Candidate's Answer
{answer}

Provide your evaluation as:
- score: integer 1–10 (1 = very poor, 10 = exceptional)
- reasoning: 2–3 sentences explaining the score, citing specific strengths or weaknesses in the answer
- better_version: a concise, improved version of the answer (1–4 sentences) that would score higher

Be honest and constructive. Adapt the better_version to match the candidate's apparent background."""
