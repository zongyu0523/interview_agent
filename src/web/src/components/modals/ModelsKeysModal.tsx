import { useState, useEffect } from "react";
import { X, Key, Cpu, MessageSquare, ScanSearch, Mic, Loader2, AlertCircle, Trash2, Check } from "lucide-react";
import {
  getApiKey, setApiKey, clearApiKey, verifyApiKey,
  getAnthropicKey, setAnthropicKey, clearAnthropicKey, verifyAnthropicKey,
} from "../../services/api";
import { useModels, useUpdateModels } from "../../hooks/useModelQueries";

// ── Model options per role ────────────────────────────────────────────────────
const LLM_OPTIONS = [
  "anthropic/claude-sonnet-4-6",
  "anthropic/claude-opus-4-6",
  "anthropic/claude-haiku-4-5-20251001",
  "openai/gpt-5",
  "openai/gpt-5-mini",
  "openai/gpt-5-nano",
  "openai/gpt-4o",
  "openai/gpt-4o-mini",
];
const TTS_OPTIONS = ["browser/tts", "openai/tts-1", "openai/tts-1-hd"];
const STT_OPTIONS = ["browser/stt", "openai/whisper-1"];

const ROLE_META: Record<string, { label: string; options: string[]; provider: "anthropic" | "openai" }> = {
  // Chat
  chat_agent:     { label: "Chat Agent",      options: LLM_OPTIONS, provider: "anthropic" },
  task_generator: { label: "Task Generator",  options: LLM_OPTIONS, provider: "anthropic" },
  // 解析
  resume_parser:  { label: "Resume Parser",   options: LLM_OPTIONS, provider: "anthropic" },
  match_analyzer: { label: "Match Analyzer",  options: LLM_OPTIONS, provider: "anthropic" },
  scorer:         { label: "Answer Scorer",   options: LLM_OPTIONS, provider: "anthropic" },
  // 語音
  tts:            { label: "Text to Speech",  options: TTS_OPTIONS, provider: "openai" },
  stt:            { label: "Speech to Text",  options: STT_OPTIONS, provider: "openai" },
};

// Grouped display order
const ROLE_GROUPS: { title: string; icon: string; roles: string[] }[] = [
  { title: "Chat",     icon: "chat",  roles: ["chat_agent", "task_generator"] },
  { title: "Analysis", icon: "parse", roles: ["resume_parser", "match_analyzer", "scorer"] },
  { title: "Voice",    icon: "voice", roles: ["tts", "stt"] },
];

// ── Types ─────────────────────────────────────────────────────────────────────
interface ModelsKeysModalProps {
  open: boolean;
  onClose: () => void;
}

// ── Helper ────────────────────────────────────────────────────────────────────
function maskKey(key: string) {
  return key ? `${key.slice(0, 6)}${"•".repeat(8)}${key.slice(-4)}` : "";
}

// ── Key Row ───────────────────────────────────────────────────────────────────
function KeyRow({
  label, description, placeholder,
  stored, maskedValue, input, verifying, error,
  onInputChange, onSave, onClear,
}: {
  label: string; description: string; placeholder: string;
  stored: boolean; maskedValue: string;
  input: string; verifying: boolean; error: string | null;
  onInputChange: (v: string) => void; onSave: () => void; onClear: () => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[13px] font-semibold text-[var(--color-text-primary)]">{label}</p>
          <p className="text-[11px] text-[var(--color-text-muted)]">{description}</p>
        </div>
        {stored && (
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-[var(--color-green)]" />
            <span className="text-[11px] text-[var(--color-green)]">Connected</span>
          </div>
        )}
      </div>

      {stored ? (
        <div className="flex h-9 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] pl-3 pr-1.5">
          <Key size={13} className="shrink-0 text-[var(--color-text-muted)]" />
          <span className="flex-1 font-mono text-[12px] text-[var(--color-text-secondary)]">{maskedValue}</span>
          <button onClick={onClear} className="flex h-7 items-center gap-1.5 rounded-md border border-red-200 bg-red-50 px-3 text-red-600 hover:bg-red-100 transition-colors">
            <Trash2 size={13} />
            <span className="text-[12px] font-medium">Remove</span>
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-1.5">
          <div className="flex h-9 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2">
            <Key size={13} className="shrink-0 text-[var(--color-text-muted)]" />
            <input
              type="password"
              placeholder={placeholder}
              value={input}
              disabled={verifying}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") onSave(); }}
              className="h-full flex-1 bg-transparent font-mono text-[12px] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none disabled:opacity-50"
            />
            <button
              onClick={onSave}
              disabled={!input.trim() || verifying}
              className="flex items-center gap-1 rounded-md bg-[var(--color-dark)] px-2.5 py-1 text-[11px] font-medium text-white disabled:opacity-40"
            >
              {verifying ? <Loader2 size={11} className="animate-spin" /> : <Check size={11} />}
              {verifying ? "Verifying..." : "Connect"}
            </button>
          </div>
          {error && (
            <div className="flex items-center gap-1.5">
              <AlertCircle size={11} className="text-red-400" />
              <span className="text-[11px] text-red-400">{error}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Modal ────────────────────────────────────────────────────────────────
export function ModelsKeysModal({ open, onClose }: ModelsKeysModalProps) {
  // ── API Key state ──
  const [anthropicInput, setAnthropicInput] = useState("");
  const [anthropicStored, setAnthropicStored] = useState(false);
  const [anthropicVerifying, setAnthropicVerifying] = useState(false);
  const [anthropicError, setAnthropicError] = useState<string | null>(null);

  const [openaiInput, setOpenaiInput] = useState("");
  const [openaiStored, setOpenaiStored] = useState(false);
  const [openaiVerifying, setOpenaiVerifying] = useState(false);
  const [openaiError, setOpenaiError] = useState<string | null>(null);


  // ── Model state ──
  const { data: serverModels = {}, isLoading: modelsLoading } = useModels();
  const updateModelsMutation = useUpdateModels();
  const [draftModels, setDraftModels] = useState<Record<string, string>>({});
  const [modelsSaved, setModelsSaved] = useState(false);

  // Load keys + models when modal opens
  useEffect(() => {
    if (!open) return;

    setAnthropicStored(getAnthropicKey() !== "");
    setOpenaiStored(getApiKey() !== "");

    setDraftModels(serverModels);
  }, [open, serverModels]);

  // ── Key handlers ──
  async function handleSaveAnthropic() {
    const key = anthropicInput.trim();
    if (!key) return;
    setAnthropicError(null);
    setAnthropicVerifying(true);
    try {
      const ok = await verifyAnthropicKey(key);
      if (ok.valid) {
        setAnthropicKey(key);
        setAnthropicStored(true);
        setAnthropicInput("");
      } else {
        setAnthropicError(ok.detail || "Invalid API key");
      }
    } catch {
      setAnthropicError("Connection failed");
    } finally {
      setAnthropicVerifying(false);
    }
  }

  async function handleClearAnthropic() {
    clearAnthropicKey();
    setAnthropicStored(false);
    setAnthropicInput("");
    setAnthropicError(null);
  }

  async function handleSaveOpenai() {
    const key = openaiInput.trim();
    if (!key) return;
    setOpenaiError(null);
    setOpenaiVerifying(true);
    try {
      const ok = await verifyApiKey(key);
      if (ok.valid) {
        setApiKey(key);
        setOpenaiStored(true);
        setOpenaiInput("");
      } else {
        setOpenaiError(ok.detail || "Invalid API key");
      }
    } catch {
      setOpenaiError("Connection failed");
    } finally {
      setOpenaiVerifying(false);
    }
  }

  async function handleClearOpenai() {
    clearApiKey();
    setOpenaiStored(false);
    setOpenaiInput("");
    setOpenaiError(null);
  }


  // ── Model handlers ──
  async function handleSaveModels() {
    updateModelsMutation.mutate(draftModels, {
      onSuccess: () => {
        setModelsSaved(true);
        setTimeout(() => setModelsSaved(false), 2000);
      }
    });
  }

  const modelsChanged = JSON.stringify(draftModels) !== JSON.stringify(serverModels);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="flex w-[480px] max-h-[85vh] flex-col rounded-[20px] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between px-5 py-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-dark)]">
              <Cpu size={16} className="text-white" />
            </div>
            <span className="text-[16px] font-semibold text-[var(--color-text-primary)]">Models & Keys</span>
          </div>
          <button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-[var(--color-hover)]">
            <X size={18} className="text-[var(--color-text-secondary)]" />
          </button>
        </div>

        <div className="h-px bg-[var(--color-border)]" />

        <div className="flex flex-col gap-4 overflow-y-auto p-5">
          {/* ── API Keys ── */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Key size={14} className="text-[var(--color-text-secondary)]" />
              <span className="text-[13px] font-semibold text-[var(--color-text-primary)]">API Keys</span>
            </div>

            <KeyRow
              label="Anthropic"
              description="Chat · Task generation · Resume parsing"
              placeholder="sk-ant-..."
              stored={anthropicStored}
              maskedValue={maskKey(getAnthropicKey())}
              input={anthropicInput}
              verifying={anthropicVerifying}
              error={anthropicError}
              onInputChange={(v) => { setAnthropicInput(v); setAnthropicError(null); }}
              onSave={handleSaveAnthropic}
              onClear={handleClearAnthropic}
            />

            <KeyRow
              label="OpenAI"
              description="Text to Speech · Speech to Text"
              placeholder="sk-..."
              stored={openaiStored}
              maskedValue={maskKey(getApiKey())}
              input={openaiInput}
              verifying={openaiVerifying}
              error={openaiError}
              onInputChange={(v) => { setOpenaiInput(v); setOpenaiError(null); }}
              onSave={handleSaveOpenai}
              onClear={handleClearOpenai}
            />

          </div>

          <div className="h-px bg-[var(--color-border)]" />

          {/* ── Models ── */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Cpu size={14} className="text-[var(--color-text-secondary)]" />
              <span className="text-[13px] font-semibold text-[var(--color-text-primary)]">Agent Models</span>
            </div>

            {modelsLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 size={18} className="animate-spin text-[var(--color-text-muted)]" />
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {ROLE_GROUPS.map((group) => {
                  const GroupIcon = group.icon === "chat"
                    ? MessageSquare
                    : group.icon === "parse"
                      ? ScanSearch
                      : Mic;

                  return (
                    <div key={group.title} className="flex flex-col gap-1.5">
                      <div className="flex items-center gap-1.5">
                        <GroupIcon size={11} className="text-[var(--color-text-muted)]" />
                        <span className="text-[10px] font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
                          {group.title}
                        </span>
                      </div>

                      {group.roles.map((role) => {
                        const meta = ROLE_META[role];
                        const current = draftModels[role] ?? "";
                        const providerReady = current.startsWith("browser/")
                          ? true
                          : current.startsWith("openai/")
                            ? openaiStored
                            : current.startsWith("anthropic/")
                              ? anthropicStored
                              : true;

                        return (
                          <div key={role} className="flex items-center gap-2">
                            <p className="w-[108px] shrink-0 text-[12px] font-medium text-[var(--color-text-primary)]">
                              {meta.label}
                            </p>
                            <select
                              value={current}
                              onChange={(e) =>
                                setDraftModels((prev) => ({ ...prev, [role]: e.target.value }))
                              }
                              className="flex-1 h-8 cursor-pointer rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 text-[11px] text-[var(--color-text-primary)] outline-none"
                            >
                              {meta.options.map((opt) => (
                                <option key={opt} value={opt}>{opt}</option>
                              ))}
                              {!meta.options.includes(current) && current && (
                                <option value={current}>{current}</option>
                              )}
                            </select>
                            <div className="w-4 shrink-0 flex items-center justify-center">
                              {!providerReady && (
                                <div title={`${current.startsWith("openai/") ? "OpenAI" : "Anthropic"} key not connected`}>
                                  <AlertCircle
                                    size={13}
                                    className="text-red-400"
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="h-px shrink-0 bg-[var(--color-border)]" />
        <div className="flex shrink-0 items-center justify-end gap-2 px-5 py-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-[13px] font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-hover)]"
          >
            Close
          </button>
          <button
            onClick={handleSaveModels}
            disabled={!modelsChanged || updateModelsMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-[var(--color-dark)] px-4 py-2 text-[13px] font-medium text-white disabled:opacity-40"
          >
            {updateModelsMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : modelsSaved ? <Check size={14} /> : null}
            {updateModelsMutation.isPending ? "Saving..." : modelsSaved ? "Saved!" : "Save Models"}
          </button>
        </div>
      </div>
    </div>
  );
}
