import { useStore } from "@/store/dashboard"

const NAV_ICONS: Record<string, string> = {
  home: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M2 7l6-5 6 5v6a1 1 0 01-1 1H3a1 1 0 01-1-1V7z"/></svg>`,
  explore: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="2"/><path d="M8 2v2M8 12v2M2 8h2M12 8h2"/></svg>`,
  timeline: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M2 4h12M2 8h8M2 12h10"/><circle cx="12" cy="4" r="1.5"/><circle cx="10" cy="8" r="1.5"/><circle cx="12" cy="12" r="1.5"/></svg>`,
  search: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/></svg>`,
  signals: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M8 2v4M8 10v4"/><circle cx="8" cy="8" r="1" fill="currentColor"/></svg>`,
  briefing: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M3 2h10a1 1 0 011 1v10a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M5 6h6M5 9h4"/></svg>`,
  alerts: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M8 2a5 5 0 00-5 5v2l-1 2h12l-1-2V7a5 5 0 00-5-5z"/><path d="M6 12a2 2 0 004 0"/></svg>`,
}

const items = [
  { id: "home", label: "Discoveries" },
  { id: "explore", label: "Relationships" },
  { id: "timeline", label: "Narratives" },
  { id: "briefing", label: "Briefing" },
  { id: "signals", label: "Signals" },
  { id: "alerts", label: "Alerts" },
  { id: "search", label: "Search" },
]

export function Sidebar({ activeTab, onTabChange }: { activeTab: string; onTabChange: (t: string) => void }) {
  const open = useStore((s) => s.sidebarOpen)

  return (
    <aside
      className={`fixed left-0 top-0 z-40 h-screen border-r border-[var(--color-border)] bg-[var(--color-bg)] transition-all duration-200 flex flex-col ${
        open ? "w-52" : "w-0 -translate-x-full overflow-hidden"
      }`}
    >
      <div className="flex h-14 items-center border-b border-[var(--color-border)] px-5 shrink-0">
        <span className="text-lg font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>np</span>
        <span className="ml-2 text-[9px] font-mono text-[var(--color-cyan)] tracking-widest uppercase">intel</span>
        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--color-green)] animate-pulseGlow" />
      </div>

      <nav className="flex-1 px-3 py-5 space-y-0.5 overflow-y-auto">
        {items.map((item) => {
          const active = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 text-xs font-mono tracking-wider uppercase rounded transition-all ${
                active
                  ? "text-[var(--color-fg)] bg-[var(--color-accent-subtle)] border-l-2 border-[var(--color-accent)]"
                  : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg-secondary)] hover:bg-[var(--color-card)] border-l-2 border-transparent"
              }`}
            >
              <span
                className="shrink-0"
                dangerouslySetInnerHTML={{ __html: NAV_ICONS[item.id] }}
                style={{ color: active ? "var(--color-accent)" : undefined }}
              />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="border-t border-[var(--color-border)] px-5 py-3 shrink-0 flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-green)]" />
        <span className="text-[9px] font-mono text-[var(--color-fg-muted)]">System Active</span>
      </div>
    </aside>
  )
}
