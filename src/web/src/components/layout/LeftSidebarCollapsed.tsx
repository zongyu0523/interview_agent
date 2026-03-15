import { PanelLeft, Plus } from "lucide-react";
import type { Application } from "../../types/resume";

interface LeftSidebarCollapsedProps {
  companies: Application[];
  activeCompanyId?: string;
  onExpand?: () => void;
  onSelectCompany?: (id: string) => void;
  onAddCompany?: () => void;
}

function nameToColor(name: string): string {
  const colors = [
    "#4285F4", "#E50914", "#0A66C2", "#1DB954",
    "#FF6900", "#7B61FF", "#00B4D8", "#E63946",
    "#2A9D8F", "#F77F00", "#6A4C93", "#1D3557",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

export function LeftSidebarCollapsed({
  companies,
  activeCompanyId,
  onExpand,
  onSelectCompany,
  onAddCompany,
}: LeftSidebarCollapsedProps) {
  return (
    <div className="flex w-14 shrink-0 flex-col items-center gap-4 rounded-[16px] border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
      <button onClick={onExpand} className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-[var(--color-hover)]">
        <PanelLeft size={18} className="text-[var(--color-text-secondary)]" />
      </button>
      <button
        onClick={onAddCompany}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-dark)]"
      >
        <Plus size={16} className="text-white" />
      </button>
      <div className="h-px w-6 bg-[var(--color-border)]" />
      <div className="flex flex-col items-center gap-2 overflow-y-auto">
        {companies.map((app) => {
          const color = nameToColor(app.company_name);
          const initial = app.company_name.charAt(0).toUpperCase();
          const isActive = app.id === activeCompanyId;

          return (
            <button
              key={app.id}
              onClick={() => onSelectCompany?.(app.id)}
              className={`flex h-8 w-8 items-center justify-center rounded-lg text-white transition-all ${
                isActive ? "ring-2 ring-[var(--color-green)] ring-offset-1 ring-offset-[var(--color-surface)]" : "opacity-60 hover:opacity-100"
              }`}
              style={{ backgroundColor: color }}
              title={`${app.company_name} - ${app.job_title}`}
            >
              <span className="text-[14px] font-semibold">{initial}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
