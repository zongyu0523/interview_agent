import { useState } from "react";
import { CircleCheck, MessageCircle, FileText, ChevronDown, ChevronUp } from "lucide-react";
import type { SessionTask } from "../../services/api";
import { getSessionReport } from "../../services/api";

interface SessionEndedProps {
  questions?: number;
  sessionId?: string;
}

export function SessionEnded({ questions = 0, sessionId }: SessionEndedProps) {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState<SessionTask[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleViewReport() {
    if (open) { setOpen(false); return; }
    if (tasks.length > 0) { setOpen(true); return; }
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await getSessionReport(sessionId);
      setTasks(data.tasks);
      setOpen(true);
    } finally {
      setLoading(false);
    }
  }

  const completed = tasks.filter((t) => t.status === "completed");
  const avgScore = completed.length
    ? Math.round(completed.reduce((sum, t) => sum + (t.score ?? 0), 0) / completed.length * 10) / 10
    : null;

  return (
    <div className="flex flex-col gap-3 bg-[var(--color-bg)] px-8 pb-8 pt-6">
      {/* Divider with badge */}
      <div className="flex w-full items-center gap-3">
        <div className="h-px flex-1 bg-[var(--color-border)]" />
        <div className="flex items-center gap-1.5 rounded-full bg-[var(--color-hover)] px-3 py-1">
          <CircleCheck size={14} className="text-[var(--color-green)]" />
          <span className="text-[12px] font-medium text-[var(--color-text-secondary)]">Interview Ended</span>
        </div>
        <div className="h-px flex-1 bg-[var(--color-border)]" />
      </div>

      {/* Session info */}
      <div className="flex items-center justify-center gap-4">
        <div className="flex items-center gap-1">
          <MessageCircle size={14} className="text-[var(--color-text-muted)]" />
          <span className="text-[13px] text-[var(--color-text-muted)]">Rounds: {questions}</span>
        </div>
        {avgScore !== null && (
          <div className="flex items-center gap-1">
            <span className="text-[13px] text-[var(--color-text-muted)]">Avg Score:</span>
            <span className="text-[13px] font-semibold text-[var(--color-text-primary)]">{avgScore} / 10</span>
          </div>
        )}
      </div>

      {/* View Report Button */}
      <button
        onClick={handleViewReport}
        disabled={loading}
        className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[var(--color-dark)] text-white disabled:opacity-50"
      >
        <FileText size={18} />
        <span className="text-[15px] font-semibold">
          {loading ? "Loading..." : "View Report"}
        </span>
        {!loading && (open ? <ChevronUp size={16} /> : <ChevronDown size={16} />)}
      </button>

      {/* Report content */}
      {open && tasks.length > 0 && (
        <div className="flex flex-col gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          {tasks.map((task, i) => (
            <div key={i} className="flex flex-col gap-1.5 border-b border-[var(--color-border)] pb-3 last:border-0 last:pb-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[13px] font-semibold text-[var(--color-text-primary)]">
                  {i + 1}. {task.topic}
                </span>
                {task.score != null ? (
                  <ScoreBadge score={task.score} />
                ) : (
                  <span className="text-[11px] text-[var(--color-text-muted)]">—</span>
                )}
              </div>
              {task.evaluation && (
                <p className="text-[12px] leading-relaxed text-[var(--color-text-secondary)]">
                  {task.evaluation}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 8 ? "bg-green-100 text-green-700" :
    score >= 5 ? "bg-yellow-100 text-yellow-700" :
    "bg-red-100 text-red-600";
  return (
    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[12px] font-semibold ${color}`}>
      {score} / 10
    </span>
  );
}
