import { Check, Loader2 } from "lucide-react";

interface GeneratingModalProps {
  open: boolean;
  step: "plan" | "start";
}

const STEPS = [
  { key: "plan", label: "Generating interview plan", desc: "Analyzing resume & job requirements" },
  { key: "start", label: "Starting interview", desc: "Preparing opening message" },
] as const;

export function GeneratingModal({ open, step }: GeneratingModalProps) {
  if (!open) return null;

  const currentIdx = STEPS.findIndex((s) => s.key === step);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0" />

      <div className="relative flex w-[360px] flex-col gap-6 rounded-[20px] bg-[var(--color-surface)] p-7 shadow-[0_16px_60px_#00000030]">
        <div className="flex flex-col gap-1">
          <span className="text-[17px] font-semibold text-[var(--color-text-primary)]">
            Setting up your interview
          </span>
          <span className="text-[13px] text-[var(--color-text-muted)]">
            This may take a few seconds...
          </span>
        </div>

        <div className="flex flex-col gap-3">
          {STEPS.map((s, i) => {
            const done = i < currentIdx;
            const active = i === currentIdx;
            return (
              <div key={s.key} className="flex items-center gap-3">
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                    done
                      ? "border-[var(--color-green)] bg-[var(--color-green)]"
                      : active
                      ? "border-[var(--color-green)]"
                      : "border-[var(--color-border)]"
                  }`}
                >
                  {done ? (
                    <Check size={14} className="text-white" strokeWidth={2.5} />
                  ) : active ? (
                    <Loader2 size={14} className="animate-spin text-[var(--color-green)]" />
                  ) : (
                    <span className="text-[12px] font-medium text-[var(--color-text-muted)]">{i + 1}</span>
                  )}
                </div>
                <div className="flex flex-col gap-0.5">
                  <span
                    className={`text-[13px] font-medium ${
                      done || active ? "text-[var(--color-text-primary)]" : "text-[var(--color-text-muted)]"
                    }`}
                  >
                    {s.label}
                  </span>
                  {active && (
                    <span className="text-[12px] text-[var(--color-text-muted)]">{s.desc}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
