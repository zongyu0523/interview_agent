import type { ResumeData, Application, Session, InterviewType, SessionMode } from "../types/resume";
import { getStoredModels } from "../hooks/useModelQueries";

// ✅ 使用環境變數控制 API URL，未設定則使用本地端
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const USER_STORAGE_KEY = "jiaf_user_id";

function getOrCreateUserId(): string {
  let id = localStorage.getItem(USER_STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(USER_STORAGE_KEY, id);
  }
  return id;
}

const USER_ID = getOrCreateUserId();

export { USER_ID };

/* ═══════════════════════════════════════════
   API Key management (localStorage)
   ═══════════════════════════════════════════ */

const OPENAI_KEY_STORAGE = "openai_api_key";
const ANTHROPIC_KEY_STORAGE = "anthropic_api_key";

// ── OpenAI Key ───────────────────────────────────────────────────────────────
export function getApiKey(): string {
  return localStorage.getItem(OPENAI_KEY_STORAGE) ?? "";
}
export function setApiKey(key: string) {
  localStorage.setItem(OPENAI_KEY_STORAGE, key);
}
export function clearApiKey() {
  localStorage.removeItem(OPENAI_KEY_STORAGE);
}

// ── Anthropic Key ────────────────────────────────────────────────────────────
export function getAnthropicKey(): string {
  return localStorage.getItem(ANTHROPIC_KEY_STORAGE) ?? "";
}
export function setAnthropicKey(key: string) {
  localStorage.setItem(ANTHROPIC_KEY_STORAGE, key);
}
export function clearAnthropicKey() {
  localStorage.removeItem(ANTHROPIC_KEY_STORAGE);
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const openaiKey = getApiKey();
  const anthropicKey = getAnthropicKey();
  return {
    "X-User-Id": USER_ID,
    "X-Models": JSON.stringify(getStoredModels()),
    ...(openaiKey ? { "X-OpenAI-Key": openaiKey } : {}),
    ...(anthropicKey ? { "X-Anthropic-Key": anthropicKey } : {}),
    ...extra,
  };
}

async function extractError(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => ({}));
  return body.detail || fallback;
}

/* ═══════════════════════════════════════════
   Key Status / Verify API
   ═══════════════════════════════════════════ */

export async function fetchBackendKeyStatus(): Promise<{ anthropic: boolean; openai: boolean }> {
  const res = await fetch(`${API_BASE}/api/key`, { headers: authHeaders() });
  if (!res.ok) return { anthropic: false, openai: false };
  const data = await res.json();
  return { anthropic: !!data.anthropic, openai: !!data.openai };
}

export async function verifyApiKey(key: string): Promise<{ valid: boolean; detail?: string }> {
  const res = await fetch(`${API_BASE}/api/key/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ openai: key }),
  });
  return res.json();
}

export async function verifyAnthropicKey(key: string): Promise<{ valid: boolean; detail?: string }> {
  const res = await fetch(`${API_BASE}/api/key/verify/anthropic`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ anthropic: key }),
  });
  return res.json();
}

/* ═══════════════════════════════════════════
   Resume API
   ═══════════════════════════════════════════ */

/** GET /api/resume */
export async function fetchResume(): Promise<ResumeData | null> {
  const res = await fetch(`${API_BASE}/api/resume`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch resume: ${res.status}`);
  return res.json();
}

/** POST /api/resume/parse — 上傳 PDF，解析後回傳結構化履歷 */
export async function parseResume(file: File): Promise<ResumeData> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/resume/parse`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) throw new Error(await extractError(res, "Parse failed"));
  return res.json();
}

/** PUT /api/resume — 手動更新履歷 */
export async function updateResume(
  data: Partial<Pick<ResumeData, "basic_info" | "professional_summary" | "interview_hooks" | "work_experience" | "education">>
): Promise<ResumeData> {
  const res = await fetch(`${API_BASE}/api/resume`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await extractError(res, "Update failed"));
  return res.json();
}

/* ═══════════════════════════════════════════
   Company / Application API
   ═══════════════════════════════════════════ */

/** GET /api/company */
export async function fetchApplications(): Promise<Application[]> {
  const res = await fetch(`${API_BASE}/api/company`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch applications: ${res.status}`);
  return res.json();
}

/** POST /api/company */
export async function createApplication(data: {
  company_name: string;
  job_title: string;
  job_description?: string;
  industry?: string;
  job_grade?: string;
}): Promise<Application> {
  const res = await fetch(`${API_BASE}/api/company`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await extractError(res, "Create failed"));
  return res.json();
}

/** DELETE /api/company/{application_id} */
export async function deleteApplication(applicationId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/company/${applicationId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await extractError(res, "Delete failed"));
}

/* ═══════════════════════════════════════════
   Session API
   ═══════════════════════════════════════════ */

/** GET /api/session/company/{company_id} */
export async function fetchSessions(companyId: string): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/api/session/company/${companyId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.status}`);
  return res.json();
}

/** POST /api/session */
export async function createSession(data: {
  company_id: string;
  type: InterviewType;
  mode: SessionMode;
  interviewer_name?: string;
  additional_notes?: string;
  must_ask_questions?: string[];
}): Promise<Session> {
  const res = await fetch(`${API_BASE}/api/session`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await extractError(res, "Create session failed"));
  return res.json();
}

/** DELETE /api/session/{session_id} */
export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await extractError(res, "Delete session failed"));
}

/* ═══════════════════════════════════════════
   Chat API
   ═══════════════════════════════════════════ */

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResult {
  response: string;
  finished: boolean;
  total_round: number;
  task_topic: string;
  task_instruction: string;
}

export interface ChatHistoryResult {
  messages: ChatMessage[];
  total_round: number;
}

/** POST /api/chat/{session_id}/start — initialize graph, returns first AI message */
export async function startInterview(sessionId: string): Promise<ChatResult> {
  const res = await fetch(`${API_BASE}/api/chat/${sessionId}/start`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await extractError(res, "Start interview failed"));
  return res.json();
}

/** POST /api/chat/{session_id} */
export async function sendMessage(sessionId: string, message: string): Promise<ChatResult> {
  const res = await fetch(`${API_BASE}/api/chat/${sessionId}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(await extractError(res, "Chat failed"));
  return res.json();
}

/** GET /api/chat/{session_id}/history */
export async function fetchChatHistory(sessionId: string): Promise<ChatHistoryResult> {
  const res = await fetch(`${API_BASE}/api/chat/${sessionId}/history`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch chat history: ${res.status}`);
  const data = await res.json();
  return { messages: data.messages, total_round: data.total_round ?? 0 };
}

/* ═══════════════════════════════════════════
   Speech API (TTS / STT)
   ═══════════════════════════════════════════ */

/** POST /api/speech/synthesize — TTS: text → streaming MP3 response */
export async function synthesizeSpeech(text: string): Promise<Response> {
  const res = await fetch(`${API_BASE}/api/speech/synthesize`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(await extractError(res, "Speech synthesis failed"));
  return res;
}

/** POST /api/speech/transcribe — STT: audio blob → text */
export async function transcribeAudio(audio: Blob): Promise<string> {
  const formData = new FormData();
  formData.append("audio", audio, "recording.webm");
  const res = await fetch(`${API_BASE}/api/speech/transcribe`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) throw new Error(await extractError(res, "Transcription failed"));
  const data = await res.json();
  return data.text;
}

/* ═══════════════════════════════════════════
   Feedback API
   ═══════════════════════════════════════════ */

export interface GrammarResult {
  corrected_version: string;
}

export interface ScoreResult {
  score: number;
  reasoning: string;
  better_version: string;
}

/** POST /api/feedback/grammar — grammar correction */
export async function getGrammarFeedback(text: string): Promise<GrammarResult> {
  const res = await fetch(`${API_BASE}/api/feedback/grammar`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(await extractError(res, "Grammar feedback failed"));
  return res.json();
}

/** POST /api/feedback/score — score and better version */
export async function getScoreFeedback(
  sessionId: string,
  question: string,
  answer: string,
  taskTopic?: string,
  taskInstruction?: string
): Promise<ScoreResult> {
  const res = await fetch(`${API_BASE}/api/feedback/score`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      session_id: sessionId,
      question,
      answer,
      task_topic: taskTopic || "",
      task_instruction: taskInstruction || "",
    }),
  });
  if (!res.ok) throw new Error(await extractError(res, "Score feedback failed"));
  return res.json();
}

/* ═══════════════════════════════════════════
   Match Analysis API
   ═══════════════════════════════════════════ */

export interface MatchAnalysisResult {
  score: number;
  label: string;
  score_reason: string;
}

/** GET /api/match/{application_id} — get existing match analysis */
export async function getMatchAnalysis(applicationId: string): Promise<MatchAnalysisResult | null> {
  const res = await fetch(`${API_BASE}/api/match/${applicationId}`, { headers: authHeaders() });
  if (!res.ok) return null;
  const data = await res.json();
  return data || null;
}

/** POST /api/match — analyze resume-job fit */
export async function analyzeMatch(applicationId: string): Promise<MatchAnalysisResult> {
  const res = await fetch(`${API_BASE}/api/match`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ user_id: USER_ID, application_id: applicationId }),
  });
  if (!res.ok) throw new Error(await extractError(res, "Match analysis failed"));
  return res.json();
}
