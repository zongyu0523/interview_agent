import { useState } from "react";
import { CircleCheck, MessageCircle, FileText, X, Star } from "lucide-react";
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
    <>
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
        </button>
      </div>

      {/* Modal */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" onClick={() => setOpen(false)}>
          <div
            className="relative flex w-full max-w-lg flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-4">
              <div className="flex flex-col gap-0.5">
                <span className="text-[16px] font-bold text-[var(--color-text-primary)]">Interview Report</span>
                {avgScore !== null && (
                  <div className="flex items-center gap-1.5">
                    <Star size={12} className="text-yellow-400" fill="currentColor" />
                    <span className="text-[12px] text-[var(--color-text-muted)]">
                      Average Score: <span className="font-semibold text-[var(--color-text-primary)]">{avgScore} / 10</span>
                    </span>
                  </div>
                )}
              </div>
              <button
                onClick={() => setOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-[var(--color-hover)]"
              >
                <X size={16} className="text-[var(--color-text-secondary)]" />
              </button>
            </div>

            {/* Task List */}
            <div className="flex flex-col gap-0 overflow-y-auto" style={{ maxHeight: "60vh" }}>
              {tasks.map((task, i) => (
                <div
                  key={i}
                  className="flex flex-col gap-2 border-b border-[var(--color-border)] px-6 py-4 last:border-0"
                >
                  {/* Topic row */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-hover)] text-[11px] font-bold text-[var(--color-text-secondary)]">
                        {i + 1}
                      </span>
                      <span className="text-[14px] font-semibold text-[var(--color-text-primary)]">{task.topic}</span>
                    </div>
                    {task.score != null ? (
                      <ScoreBadge score={task.score} />
                    ) : (
                      <span className="shrink-0 text-[12px] text-[var(--color-text-muted)]">Skipped</span>
                    )}
                  </div>

                  {/* Score bar */}
                  {task.score != null && (
                    <div className="ml-7 h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-hover)]">
                      <div
                        className={`h-full rounded-full transition-all ${scoreBarColor(task.score)}`}
                        style={{ width: `${task.score * 10}%` }}
                      />
                    </div>
                  )}

                  {/* Evaluation */}
                  {task.evaluation && (
                    <p className="ml-7 text-[12px] leading-relaxed text-[var(--color-text-secondary)]">
                      {task.evaluation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 8 ? "bg-green-100 text-green-700" :
    score >= 5 ? "bg-yellow-100 text-yellow-700" :
    "bg-red-100 text-red-600";
  return (
    <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[12px] font-bold ${color}`}>
      {score} / 10
    </span>
  );
}

function scoreBarColor(score: number) {
  if (score >= 8) return "bg-green-400";
  if (score >= 5) return "bg-yellow-400";
  return "bg-red-400";
}
