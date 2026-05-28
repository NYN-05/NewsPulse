import { useStore } from "@/store/dashboard"

export function Header({ onSearchClick }: { onSearchClick?: () => void }) {
  const { toggleSidebar, lastUpdated } = useStore()

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-[var(--color-border)] bg-[var(--color-bg)]/90 backdrop-blur-md px-5">
      <button
        onClick={toggleSidebar}
        className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors text-xs"
      >
        ≡
      </button>

      <div className="flex-1" />

      <button
        onClick={onSearchClick}
        className="hidden sm:flex items-center gap-2 text-xs text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors border border-[var(--color-border)] rounded px-2.5 py-1"
      >
        <span className="font-mono">/</span>
        <span>Search</span>
        <span className="text-[10px] text-[var(--color-fg-muted)] border-l border-[var(--color-border)] pl-1.5 ml-1">⌘K</span>
      </button>

      {lastUpdated && (
        <span className="ml-3 text-[10px] text-[var(--color-fg-muted)] font-mono hidden md:inline">
          {new Date(lastUpdated).toLocaleTimeString()}
        </span>
      )}
    </header>
  )
}
