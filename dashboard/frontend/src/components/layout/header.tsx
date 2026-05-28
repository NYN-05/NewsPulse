import { useStore } from "@/store/dashboard"

export function Header() {
  const { toggleSidebar, toggleDark, darkMode, filters, setFilters } = useStore()

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-[var(--color-border)] bg-[var(--color-background)] px-4">
      <button onClick={toggleSidebar} className="rounded-lg p-1.5 hover:bg-[var(--color-muted)]">
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div className="flex items-center gap-2 text-sm">
        <span className="text-[var(--color-muted-foreground)]">Days:</span>
        <select
          value={filters.days}
          onChange={(e) => setFilters({ days: Number(e.target.value) })}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)] px-2 py-1 text-sm"
        >
          <option value={7}>7</option>
          <option value={14}>14</option>
          <option value={30}>30</option>
          <option value={90}>90</option>
        </select>
      </div>

      <div className="flex-1" />

      <button onClick={toggleDark} className="rounded-lg p-1.5 hover:bg-[var(--color-muted)]">
        {darkMode ? "☀️" : "🌙"}
      </button>
    </header>
  )
}
