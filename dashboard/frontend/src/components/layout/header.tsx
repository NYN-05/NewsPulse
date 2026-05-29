import { useStore } from "@/store/dashboard"

function timeAgo(iso: string | null): string {
  if (!iso) return "never"
  const diff = Date.now() - new Date(iso).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return "just now"
  if (min < 60) return `${min}m ago`
  const hrs = Math.floor(min / 60)
  if (hrs < 24) return `${hrs}h ${min % 60}m ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export function Header({ onSearchClick }: { onSearchClick?: () => void }) {
  const { toggleSidebar, pipeline } = useStore()
  const isRunning = pipeline?.status === "running"
  const isError = pipeline?.status === "error"
  const dotColor = isRunning ? "var(--color-amber)" : isError ? "var(--color-red)" : "var(--color-green)"
  const dotPulse = isRunning ? "animate-pulseGlow" : ""

  return (
    <header className="sticky top-0 z-30 flex h-12 items-center border-b border-[var(--color-border)] bg-[var(--color-bg)]/90 backdrop-blur-md px-5 gap-4">
      <button
        onClick={toggleSidebar}
        className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <path d="M2 4h12M2 8h12M2 12h12" />
        </svg>
      </button>

      <div className="flex items-center gap-3 text-[10px] font-mono text-[var(--color-fg-muted)]">
        <span className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${dotPulse}`} style={{ background: dotColor }} />
          <span>{isRunning ? "Processing" : isError ? "Error" : "Live"}</span>
        </span>
        {pipeline?.last_run_at && (
          <span className="hidden sm:inline">
            Updated {timeAgo(pipeline.last_run_at)}
            {pipeline.last_run_duration && ` · ${pipeline.last_run_duration}s`}
          </span>
        )}
      </div>

      {pipeline && pipeline.run_count > 0 && (
        <span className="hidden md:inline text-[9px] font-mono text-[var(--color-fg-muted)] opacity-60">
          {pipeline.run_count} runs · {pipeline.articles_analyzed} articles
        </span>
      )}

      <div className="flex-1" />

      <button
        onClick={onSearchClick}
        className="flex items-center gap-2 px-3 py-1.5 border border-[var(--color-border)] rounded text-[11px] font-mono text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] hover:border-[var(--color-border-hover)] transition-colors"
      >
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <circle cx="7" cy="7" r="4.5" />
          <path d="M10.5 10.5L14 14" />
        </svg>
        <span className="hidden sm:inline">Intelligence Search</span>
        <span className="text-[9px] text-[var(--color-fg-muted)] border-l border-[var(--color-border)] pl-1.5 ml-1">Ctrl+K</span>
      </button>
    </header>
  )
}
