import { useState, useEffect } from "react";
import { X, UserSearch, Code, Briefcase, HeartHandshake, Play, Keyboard, Mic, Loader2 } from "lucide-react";
import type { InterviewType, SessionMode } from "../../types/resume";

interface NewSessionModalProps {
  open: boolean;
  applicationId?: string;
  onClose: () => void;
  onStart: (data: {
    type: InterviewType;
    mode: SessionMode;
    interviewerName: string;
    notes: string;
    mustAskQuestions: string[];
  }) => Promise<void>;
}

const interviewTypes: { type: InterviewType; label: string; desc: string; icon: React.ReactNode }[] = [
  { type: "recruiter", label: "Recruiter", desc: "Initial screening call", icon: <UserSearch size={20} /> },
  { type: "technical", label: "Technical", desc: "Coding & system design", icon: <Code size={20} /> },
  { type: "hiring_manager", label: "Hiring Manager", desc: "Team fit & leadership", icon: <Briefcase size={20} /> },
  { type: "behavioral", label: "Behavioral", desc: "STAR method questions", icon: <HeartHandshake size={20} /> },
];

export function NewSessionModal({ open, applicationId, onClose, onStart }: NewSessionModalProps) {
  const [selectedType, setSelectedType] = useState<InterviewType>("recruiter");
  const [selectedMode, setSelectedMode] = useState<SessionMode>("practice");
  const [interviewerName, setInterviewerName] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setSelectedType("recruiter");
      setSelectedMode("practice");
      setInterviewerName("");
      setNotes("");
      setError(null);
    }
  }, [open]);

  if (!open) return null;

  async function handleStart() {
    if (!applicationId) return;
    setSubmitting(true);
    setError(null);
    try {
      await onStart({
        type: selectedType,
        mode: selectedMode,
        interviewerName: interviewerName.trim(),
        notes: notes.trim(),
        mustAskQuestions: [],
      });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create session");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div className="absolute inset-0 bg-transparent" onClick={onClose} />

      {/* Modal */}
      <div className="relative flex w-[520px] max-h-[90vh] flex-col gap-5 overflow-auto rounded-[20px] bg-[var(--color-surface)] p-6 shadow-[0_8px_40px_#00000020]">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="text-[18px] font-semibold text-[var(--color-text-primary)]">New Session</span>
          <button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-[var(--color-hover)]">
            <X size={18} className="text-[var(--color-text-secondary)]" />
          </button>
        </div>

        <span className="text-[14px] text-[var(--color-text-secondary)]">
          Select an interview type to start practicing
        </span>

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-[13px] text-red-600">{error}</div>
        )}

        {/* Mode Selector */}
        <div className="flex h-11 gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] p-1">
          <button
            onClick={() => setSelectedMode("practice")}
            className={`flex flex-1 items-center justify-center gap-2 rounded-[10px] ${
              selectedMode === "practice"
                ? "bg-[var(--color-surface)] shadow-[0_1px_3px_#00000010]"
                : ""
            }`}
          >
            <Keyboard size={16} className={selectedMode === "practice" ? "text-[var(--color-text-primary)]" : "text-[var(--color-text-muted)]"} />
            <span className={`text-[13px] ${selectedMode === "practice" ? "font-semibold text-[var(--color-text-primary)]" : "font-medium text-[var(--color-text-muted)]"}`}>
              Practice
            </span>
          </button>
          <button
            onClick={() => setSelectedMode("real")}
            className={`flex flex-1 items-center justify-center gap-2 rounded-[10px] ${
              selectedMode === "real"
                ? "bg-[var(--color-surface)] shadow-[0_1px_3px_#00000010]"
                : ""
            }`}
          >
            <Mic size={16} className={selectedMode === "real" ? "text-[var(--color-text-primary)]" : "text-[var(--color-text-muted)]"} />
            <span className={`text-[13px] ${selectedMode === "real" ? "font-semibold text-[var(--color-text-primary)]" : "font-medium text-[var(--color-text-muted)]"}`}>
              Real Interview
            </span>
          </button>
        </div>

        {/* Interview Types Grid */}
        <div className="flex flex-col gap-3">
          <div className="flex gap-3">
            {interviewTypes.slice(0, 2).map((t) => (
              <InterviewTypeCard
                key={t.type}
                {...t}
                selected={selectedType === t.type}
                onSelect={() => setSelectedType(t.type)}
              />
            ))}
          </div>
          <div className="flex gap-3">
            {interviewTypes.slice(2).map((t) => (
              <InterviewTypeCard
                key={t.type}
                {...t}
                selected={selectedType === t.type}
                onSelect={() => setSelectedType(t.type)}
              />
            ))}
          </div>
        </div>

        {/* Input Fields */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <span className="text-[13px] font-medium text-[var(--color-text-primary)]">Interviewer Name</span>
            <input
              type="text"
              value={interviewerName}
              onChange={(e) => setInterviewerName(e.target.value)}
              placeholder="Enter interviewer name (optional)"
              className="h-11 rounded-[10px] border border-[var(--color-border)] bg-[var(--color-bg)] px-3.5 text-[13px] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <span className="text-[13px] font-medium text-[var(--color-text-primary)]">Additional Notes</span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g., Focus on my resume experience..."
              className="h-[72px] resize-none rounded-[10px] border border-[var(--color-border)] bg-[var(--color-bg)] p-3.5 text-[13px] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
            />
          </div>
        </div>

        {/* Start Button */}
        <button
          onClick={handleStart}
          disabled={!applicationId || submitting}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[var(--color-dark)] text-white disabled:opacity-40"
        >
          {submitting ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Play size={18} />
          )}
          <span className="text-[15px] font-semibold">
            {submitting ? "Creating..." : "Start Interview"}
          </span>
        </button>
      </div>
    </div>
  );
}

function InterviewTypeCard({
  type: _type,
  label,
  desc,
  icon,
  selected,
  onSelect,
}: {
  type: InterviewType;
  label: string;
  desc: string;
  icon: React.ReactNode;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`flex flex-1 flex-col gap-3 rounded-[16px] border p-4 text-left transition-colors ${
        selected
          ? "border-[var(--color-text-primary)] bg-[var(--color-hover)]"
          : "border-[var(--color-border)] bg-[var(--color-bg)] hover:border-[var(--color-text-muted)]"
      }`}
    >
      <div className={selected ? "text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)]"}>
        {icon}
      </div>
      <div className="flex flex-col gap-1">
        <span className="text-[14px] font-medium text-[var(--color-text-primary)]">{label}</span>
        <span className="text-[12px] text-[var(--color-text-secondary)]">{desc}</span>
      </div>
    </button>
  );
}
