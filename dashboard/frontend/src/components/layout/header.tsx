import { useStore } from "@/store/dashboard"

export function Header({ onSearchClick }: { onSearchClick?: () => void }) {
  const { toggleSidebar, lastUpdated } = useStore()

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
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-green)]" />
          <span>Live</span>
        </span>
        {lastUpdated && (
          <span className="hidden sm:inline">
            Updated: {new Date(lastUpdated).toLocaleTimeString()}
          </span>
        )}
      </div>

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
