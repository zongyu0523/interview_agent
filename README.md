# Interview Agent

An AI-powered mock interview coach. Practice technical and behavioral interviews with real-time feedback, resume parsing, and session tracking.

**Live Demo**: [https://www.openagentsbox.com/interview](https://www.openagentsbox.com/interview)

---

## Features

- **Mock Interviews** — Conduct full mock interviews in text or voice mode. Choose interview type (technical, behavioral, system design) and difficulty.
- **Resume Parsing** — Upload a PDF resume and have it automatically parsed into structured data to personalize interview questions.
- **Real-time Scoring** — Get scored on each answer with detailed feedback after the session.
- **Session History** — Review past interview sessions, transcripts, and performance reports.
- **Job Match Analysis** — Paste a job description to get a match analysis against your resume.
- **Multi-model Support** — Works with Anthropic (Claude) and OpenAI (GPT) models. Switch models per role in settings.

---

## Quick Start (Online)

Visit [https://www.openagentsbox.com/interview](https://www.openagentsbox.com/interview) — no installation needed.

1. Click the key icon (top-right) to set your **Anthropic** or **OpenAI** API key.
2. Add a company and create a new interview session.
3. Start practicing.

Your API key is stored locally in your browser and never sent to our servers except to forward to the LLM provider.

---

## Self-hosting (Docker)

Run the full stack locally with a single Docker image (frontend + backend bundled together).

**Requirements**: Docker

### 1. Build

```bash
docker build -f Dockerfile.standalone -t interview-standalone .
```

### 2. Set up environment variables

Copy the example env file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### 3. Run

**Windows (PowerShell):**

```powershell
docker run -p 8000:8000 --env-file .env -v "${PWD}\data:/app/data" interview-standalone
```

**macOS / Linux:**

```bash
docker run -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" interview-standalone
```

Open [http://localhost:8000/interview](http://localhost:8000/interview) in your browser.

> **Data persistence**: All your data (resume, companies, sessions, reports) is stored in the `data/` folder on your local machine. Deleting or recreating the container will not affect your data as long as you keep the `data/` folder and mount it with `-v`.

---

## Agent Core Concept

The interview agent is built around a **tool-loop** pattern inspired by Claude Code's task tracking:

The LLM is given a pre-generated task list (interview questions/topics) at session start. On every user reply, the agent runs a `while True` loop:

1. **`check_task`** — reads the current task list and which task is `in_progress`
2. The LLM conducts the interview, asking follow-up questions as needed
3. **`update_task`** — when the candidate has sufficiently answered, mark the task complete with a score (1–10) and a private evaluation note
4. Move to the next task — repeat until all tasks are `completed`
5. Return final reply with `all_finished = True` → frontend shows the session end screen

This gives the agent a persistent, inspectable sense of progress across multi-turn conversations without relying on the LLM's memory alone.

---

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Free to use and modify for non-commercial purposes. Attribution required.

---

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + LiteLLM + Instructor
- **LLM**: Anthropic Claude / OpenAI GPT (user-provided API key)
