import { useStore } from "@/store/dashboard"

export function Header({ onSearchClick }: { onSearchClick?: () => void }) {
  const { toggleSidebar, lastUpdated } = useStore()

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-[var(--color-border)] bg-[var(--color-bg)]/80 backdrop-blur-md px-5">
      <button onClick={toggleSidebar} className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors font-mono text-xs tracking-widest">
        ≡
      </button>

      <div className="flex-1" />

      <button onClick={onSearchClick} className="hidden sm:flex items-center gap-2 px-2.5 py-1 border border-[var(--color-border)] rounded text-xs font-mono text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] hover:border-[var(--color-border-hover)] transition-colors">
        <span className="text-[var(--color-fg-muted)]">/</span>
        <span className="tracking-wide">Search</span>
        <span className="text-[9px] text-[var(--color-fg-muted)] border-l border-[var(--color-border)] pl-1.5 ml-1">⌘K</span>
      </button>

      {lastUpdated && (
        <span className="ml-3 text-[10px] font-mono text-[var(--color-fg-muted)] hidden md:inline">
          {new Date(lastUpdated).toLocaleTimeString()}
        </span>
      )}
    </header>
  )
}
