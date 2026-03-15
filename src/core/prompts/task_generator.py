"""
init_task_generate_node 的 system prompt。
使用 Anthropic content blocks 格式組裝，靜態區塊可套用 prompt caching。

輸出：list[dict]  可直接傳入 client.messages.create(system=...)
"""

# ── Part 1: 四種面試類型的核心身份與原則（靜態，可 cache）─────────────────────

_PART1: dict[str, str] = {
    "recruiter": """\
<role>
You are an expert recruiter interview planner.
</role>

<goal>
Generate a structured task list for an initial HR screening call.
Focus areas: candidate motivation, culture fit, background overview, compensation expectations, availability timeline.
</goal>

<rules>
- Tasks must be conversational and open-ended
- Avoid deep technical questions
- Cover: motivation (1), background (1), expectations (1), culture fit (1–2)
- Total: 4–5 tasks
</rules>""",

    "technical": """\
<role>
You are an expert technical interview planner at senior engineer level.
</role>

<goal>
Generate a structured task list for a technical interview.
Focus areas: core technical concepts relevant to the role, problem-solving depth, system design, real project experience.
</goal>

<rules>
- Progress from fundamentals to depth
- Ground each task in the candidate's actual skills and project experience
- Each task must specify what to probe and what follow-ups to use
- Avoid yes/no questions — surface reasoning and depth
- Total: 5–7 tasks
</rules>""",

    "behavioral": """\
<role>
You are an expert behavioral interview planner using the STAR methodology.
</role>

<goal>
Generate a structured task list for a behavioral interview.
Focus areas: past experiences, teamwork, conflict resolution, ownership, failure and learning.
</goal>

<rules>
- Each task must ask for a specific past situation, not hypotheticals
- Ground tasks in the candidate's actual work history and notable projects
- Include follow-up probes: outcome, lessons learned, what would you do differently
- Must cover: collaboration, conflict, ownership, failure
- Total: 4–6 tasks
</rules>""",

    "hiring_manager": """\
<role>
You are an expert hiring manager interview planner.
</role>

<goal>
Generate a structured task list for a final hiring manager interview.
Focus areas: strategic thinking, team fit, career trajectory, leadership style, vision alignment.
</goal>

<rules>
- Tasks should be high-level and strategic, not purely technical
- Use the candidate's career arc to probe motivation and long-term fit
- Must include: career motivation, leadership style, handling ambiguity, long-term goals
- Total: 4–5 tasks
</rules>""",
}

# ── Part 4: 長期記憶佔位（靜態）──────────────────────────────────────────────

_PART4 = """\
<long_term_memory>
(reserved — no historical performance data available at this time)
</long_term_memory>"""

# ── Output 指令（靜態）────────────────────────────────────────────────────────

_OUTPUT_RULES = """\
<output_instructions>
Each task must have:
  "topic"       — short human-readable label (5–8 words)
  "instruction" — one concise sentence summarizing what to probe (max 30 words, no follow-up lists)
  "status"      — always "pending"
</output_instructions>"""


# ── Part 2: 依 type 選擇相關的 resume 欄位 ────────────────────────────────────

def _part2_candidate(interview_type: str, resume: dict) -> str:
    basic = resume.get("basic_info", {})
    summary = resume.get("professional_summary", "")
    hooks = resume.get("interview_hooks", [])
    work_exps = resume.get("work_experience", [])
    education = resume.get("education", [])

    lines = ["<candidate_context>"]

    if interview_type == "recruiter":
        # 給高層次背景：姓名、地點、語言、摘要、工作經歷（淺）、學歷
        if basic.get("name"):
            lines.append(f"  <name>{basic['name']}</name>")
        if basic.get("location"):
            lines.append(f"  <location>{basic['location']}</location>")
        if basic.get("languages"):
            lines.append(f"  <languages>{', '.join(basic['languages'])}</languages>")
        if summary:
            lines.append(f"  <professional_summary>{summary}</professional_summary>")
        if work_exps:
            lines.append("  <work_experience>")
            for exp in work_exps:
                lines.append(f"    <job>{exp.get('role', '')} at {exp.get('company', '')} ({exp.get('date_range', '')})</job>")
            lines.append("  </work_experience>")
        if education:
            lines.append("  <education>")
            for edu in education:
                lines.append(f"    <degree>{edu.get('degree', '')} in {edu.get('major', '')} — {edu.get('school', '')} ({edu.get('graduation_year', '')})</degree>")
            lines.append("  </education>")

    elif interview_type == "technical":
        # 給技術細節：技能、interview_hooks（工作/專案來源）、工作經歷（含 responsibilities）
        if basic.get("hard_skills"):
            lines.append(f"  <hard_skills>{', '.join(basic['hard_skills'])}</hard_skills>")
        if hooks:
            lines.append("  <notable_topics>")
            for h in hooks:
                lines.append(f"    <topic source=\"{h.get('source_type', '')}\">{h.get('topic_name', '')}: {h.get('key_details', '')}</topic>")
            lines.append("  </notable_topics>")
        if work_exps:
            lines.append("  <work_experience>")
            for exp in work_exps:
                lines.append(f"    <job>{exp.get('role', '')} at {exp.get('company', '')} ({exp.get('date_range', '')})</job>")
                if exp.get("responsibilities_and_achievements"):
                    lines.append(f"    <details>{exp['responsibilities_and_achievements']}</details>")
            lines.append("  </work_experience>")

    elif interview_type == "behavioral":
        # 給行為細節：摘要、完整工作經歷、所有 interview_hooks
        if summary:
            lines.append(f"  <professional_summary>{summary}</professional_summary>")
        if work_exps:
            lines.append("  <work_experience>")
            for exp in work_exps:
                lines.append(f"    <job>{exp.get('role', '')} at {exp.get('company', '')} ({exp.get('date_range', '')})</job>")
                if exp.get("responsibilities_and_achievements"):
                    lines.append(f"    <details>{exp['responsibilities_and_achievements']}</details>")
            lines.append("  </work_experience>")
        if hooks:
            lines.append("  <notable_topics>")
            for h in hooks:
                lines.append(f"    <topic source=\"{h.get('source_type', '')}\">{h.get('topic_name', '')}: {h.get('key_details', '')}</topic>")
            lines.append("  </notable_topics>")

    elif interview_type == "hiring_manager":
        # 給策略視角：摘要、工作經歷（淺）、interview_hooks、學歷
        if summary:
            lines.append(f"  <professional_summary>{summary}</professional_summary>")
        if work_exps:
            lines.append("  <work_experience>")
            for exp in work_exps:
                lines.append(f"    <job>{exp.get('role', '')} at {exp.get('company', '')} ({exp.get('date_range', '')})</job>")
            lines.append("  </work_experience>")
        if hooks:
            lines.append("  <notable_topics>")
            for h in hooks:
                lines.append(f"    <topic>{h.get('topic_name', '')}: {h.get('key_details', '')}</topic>")
            lines.append("  </notable_topics>")
        if education:
            lines.append("  <education>")
            for edu in education:
                lines.append(f"    <degree>{edu.get('degree', '')} in {edu.get('major', '')} — {edu.get('school', '')} ({edu.get('graduation_year', '')})</degree>")
            lines.append("  </education>")

    if len(lines) == 1:
        lines.append("  (no candidate info available)")

    lines.append("</candidate_context>")
    return "\n".join(lines)


# ── Part 3: 公司與職位資訊 ─────────────────────────────────────────────────────

def _part3_company(
    company_name: str,
    job_title: str,
    industry: str,
    job_description: str,
    additional_notes: str,
    must_ask_questions: list[str],
) -> str:
    lines = [
        "<company_context>",
        f"  <company>{company_name}</company>",
        f"  <role>{job_title}</role>",
    ]
    if industry:
        lines.append(f"  <industry>{industry}</industry>")
    if job_description:
        lines.append(f"  <job_description>\n{job_description}\n  </job_description>")
    if additional_notes:
        lines.append(f"  <additional_notes>{additional_notes}</additional_notes>")
    if must_ask_questions:
        lines.append("  <must_ask_topics>")
        for q in must_ask_questions:
            lines.append(f"    <topic>{q}</topic>")
        lines.append("  </must_ask_topics>")
    lines.append("</company_context>")
    return "\n".join(lines)


# ── 主要對外函式 ───────────────────────────────────────────────────────────────

def build_task_generator_prompt(
    interview_type: str,
    resume: dict,
    company_name: str,
    job_title: str,
    industry: str = "",
    job_description: str = "",
    additional_notes: str = "",
    must_ask_questions: list[str] | None = None,
) -> list[dict]:
    """
    回傳 Anthropic system content blocks list。
    靜態區塊（Part 1, 4, output rules）標記 cache_control 供 prompt caching 使用。
    動態區塊（Part 2, 3）每次依參數組裝。
    """
    identity = _PART1.get(interview_type, _PART1["recruiter"])

    return [
        # Part 1 — 靜態，可 cache
        {
            "type": "text",
            "text": identity,
            "cache_control": {"type": "ephemeral"},
        },
        # Part 2 — 動態：依 type 篩選的候選人履歷
        {
            "type": "text",
            "text": _part2_candidate(interview_type, resume),
        },
        # Part 3 — 動態：公司與職位資訊
        {
            "type": "text",
            "text": _part3_company(
                company_name, job_title, industry,
                job_description, additional_notes,
                must_ask_questions or [],
            ),
        },
        # Part 4 — 靜態佔位，可 cache
        {
            "type": "text",
            "text": _PART4,
            "cache_control": {"type": "ephemeral"},
        },
        # Output rules — 靜態，可 cache
        {
            "type": "text",
            "text": _OUTPUT_RULES,
            "cache_control": {"type": "ephemeral"},
        },
    ]
