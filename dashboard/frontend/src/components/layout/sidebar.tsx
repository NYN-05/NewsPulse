import { useStore } from "@/store/dashboard"

const navItems = [
  { id: "home", label: "Intelligence" },
  { id: "explore", label: "Explore" },
  { id: "timeline", label: "Timeline" },
  { id: "search", label: "Search" },
  { id: "signals", label: "Signals" },
  { id: "settings", label: "Settings" },
]

export function Sidebar({ activeTab, onTabChange }: { activeTab: string; onTabChange: (t: string) => void }) {
  const { sidebarOpen } = useStore()

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] transition-all duration-200 ${
        sidebarOpen ? "w-48" : "w-0 -translate-x-full overflow-hidden"
      }`}
    >
      <div className="flex h-14 shrink-0 items-center px-5 border-b border-[var(--color-border)]">
        <span className="font-mono text-sm font-semibold tracking-tight text-[var(--color-fg)]">np</span>
        <span className="ml-2 text-[10px] text-[var(--color-fg-muted)] font-mono">intel</span>
      </div>
      <nav className="flex-1 px-3 py-6 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`w-full text-left px-3 py-1.5 text-sm rounded transition-colors ${
              activeTab === item.id
                ? "bg-[var(--color-card)] text-[var(--color-fg)]"
                : "text-[var(--color-fg-secondary)] hover:text-[var(--color-fg)]"
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="shrink-0 border-t border-[var(--color-border)] px-5 py-3">
        <p className="text-[10px] text-[var(--color-fg-muted)] font-mono">v2.0</p>
      </div>
    </aside>
  )
}
