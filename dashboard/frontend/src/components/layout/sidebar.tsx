import { useStore } from "@/store/dashboard"
import { cn } from "@/lib/utils"

const navItems = [
  { id: "overview", label: "Overview", icon: "◉" },
  { id: "sentiment", label: "Sentiment", icon: "☰" },
  { id: "categories", label: "Categories", icon: "⊞" },
  { id: "clusters", label: "Topic Clusters", icon: "◎" },
  { id: "trends", label: "Trends", icon: "↗" },
  { id: "entity-graph", label: "Entity Graph", icon: "✦" },
  { id: "entity-trends", label: "Entity Trends", icon: "⇈" },
  { id: "breaking", label: "Breaking News", icon: "⚡" },
  { id: "virality", label: "Virality", icon: "🔥" },
  { id: "bias", label: "Bias & Reliability", icon: "⚖" },
  { id: "evolution", label: "Topic Evolution", icon: "◈" },
  { id: "search", label: "Semantic Search", icon: "⌕" },
  { id: "data", label: "Data Explorer", icon: "⊟" },
]

export function Sidebar({ activeTab, onTabChange }: { activeTab: string; onTabChange: (t: string) => void }) {
  const { sidebarOpen } = useStore()

  return (
    <aside className={cn(
      "fixed left-0 top-0 z-40 h-screen border-r border-[var(--color-border)] bg-[var(--color-sidebar)] transition-all duration-200",
      sidebarOpen ? "w-56" : "w-0 overflow-hidden",
    )}>
      <div className="flex h-14 items-center gap-2 border-b border-[var(--color-border)] px-4">
        <span className="text-lg">📡</span>
        <span className="font-bold tracking-tight">NewsPulse</span>
      </div>
      <nav className="overflow-y-auto p-2" style={{ height: "calc(100vh - 56px)" }}>
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              activeTab === item.id
                ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                : "text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)]",
            )}
          >
            <span className="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}
