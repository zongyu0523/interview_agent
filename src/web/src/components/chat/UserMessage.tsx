import { Sparkles } from "lucide-react";

interface UserMessageProps {
  text: string;
  initials?: string;
  onScore?: () => void;
  scoreExpanded?: boolean;
  scoreContent?: React.ReactNode;
}

export function UserMessage({
  text,
  initials = "JD",
  onScore,
  scoreExpanded,
  scoreContent,
}: UserMessageProps) {
  return (
    <div className="flex w-full justify-end gap-3">
      {/* Bubble */}
      <div className="flex w-[480px] flex-col gap-3 rounded-[16px] bg-[var(--color-dark)] p-4">
        <p className="text-[14px] leading-[1.5] text-white">{text}</p>

        {/* Action Bar */}
        <div className="flex items-center gap-2">
          <button onClick={onScore} className="flex items-center gap-1.5 rounded-md bg-[var(--color-yellow-light)] px-2.5 py-0 h-7">
            <Sparkles size={14} className="text-[var(--color-yellow)]" />
            <span className="text-[12px] font-medium text-[var(--color-yellow)]">Score & Better</span>
          </button>
        </div>

        {/* Score Expanded Panel */}
        {scoreExpanded && scoreContent}
      </div>

      {/* Avatar */}
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--color-indigo)]">
        <span className="text-[14px] font-semibold text-white">{initials}</span>
      </div>
    </div>
  );
}
