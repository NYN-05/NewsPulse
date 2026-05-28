import { Moon, Sun, Menu, Search } from "lucide-react"
import { useStore } from "@/store/dashboard"

export function Header({ onSearchClick }: { onSearchClick?: () => void }) {
  const { toggleSidebar, toggleDark, darkMode, filters, setFilters } = useStore()

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-background)]/80 px-4 backdrop-blur-md">
      <button onClick={toggleSidebar} className="rounded-lg p-1.5 hover:bg-[var(--color-muted)] transition-colors">
        <Menu className="h-5 w-5" />
      </button>

      <button
        onClick={onSearchClick}
        className="hidden sm:flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)]/50 px-3 py-1.5 text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors min-w-[200px]"
      >
        <Search className="h-3.5 w-3.5" />
        <span>Search articles...</span>
        <span className="ml-auto text-[10px] border border-[var(--color-border)] rounded px-1">Ctrl+K</span>
      </button>

      <div className="flex items-center gap-2 ml-auto">
        <div className="flex items-center gap-1.5 text-sm">
          <span className="text-xs text-[var(--color-muted-foreground)] hidden sm:inline">Period:</span>
          <select
            value={filters.days}
            onChange={(e) => setFilters({ days: Number(e.target.value) })}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)] px-2 py-1 text-xs outline-none"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
        </div>

        <button
          onClick={toggleDark}
          className="rounded-lg p-1.5 hover:bg-[var(--color-muted)] transition-colors"
          title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
      </div>
    </header>
  )
}
