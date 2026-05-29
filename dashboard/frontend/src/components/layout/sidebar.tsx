import { useStore } from "@/store/dashboard"

const items = [
  { id: "home", label: "Discoveries" },
  { id: "explore", label: "Relationships" },
  { id: "timeline", label: "Timeline" },
  { id: "search", label: "Search" },
  { id: "signals", label: "Signals" },
]

export function Sidebar({ activeTab, onTabChange }: { activeTab: string; onTabChange: (t: string) => void }) {
  const open = useStore((s) => s.sidebarOpen)

  return (
    <aside className={`fixed left-0 top-0 z-40 h-screen border-r border-[var(--color-border)] bg-[var(--color-bg)] transition-all duration-200 ${open ? "w-52" : "w-0 -translate-x-full overflow-hidden"}`}>
      <div className="flex h-14 items-center border-b border-[var(--color-border)] px-5">
        <span className="font-serif text-lg text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>np</span>
        <span className="ml-2 text-[10px] font-mono text-[var(--color-fg-muted)]">intel</span>
      </div>
      <nav className="px-3 py-6 space-y-0.5">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`w-full text-left px-3 py-2 text-xs font-mono tracking-wider uppercase transition-colors ${
              activeTab === item.id
                ? "text-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="absolute bottom-0 left-0 right-0 border-t border-[var(--color-border)] px-5 py-3">
        <p className="text-[9px] font-mono text-[var(--color-fg-muted)]">v2.0</p>
      </div>
    </aside>
  )
}
