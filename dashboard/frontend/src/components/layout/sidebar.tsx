import { useStore } from "@/store/dashboard"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard, TrendingUp, Zap, Flame,
  BarChart3, FolderTree, Layers, LineChart,
  Share2, GitBranch, BookOpen, Target,
  Search, Table2, Scale, ShieldCheck,
} from "lucide-react"

const navGroups = [
  {
    label: "Dashboard",
    items: [
      { id: "overview", label: "Overview", icon: LayoutDashboard },
    ],
  },
  {
    label: "Trending",
    items: [
      { id: "trends", label: "Trending Topics", icon: TrendingUp },
      { id: "breaking", label: "Breaking News", icon: Zap },
      { id: "virality", label: "Virality", icon: Flame },
    ],
  },
  {
    label: "Analysis",
    items: [
      { id: "sentiment", label: "Sentiment", icon: BarChart3 },
      { id: "categories", label: "Categories", icon: FolderTree },
      { id: "clusters", label: "Topic Clusters", icon: Layers },
      { id: "evolution", label: "Topic Evolution", icon: LineChart },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { id: "entity-graph", label: "Entity Graph", icon: Share2 },
      { id: "cross-domain", label: "Cross-Domain", icon: GitBranch },
      { id: "entity-trends", label: "Entity Trends", icon: BarChart3 },
      { id: "narratives", label: "Narratives", icon: BookOpen },
      { id: "influence", label: "Influence Map", icon: Target },
    ],
  },
  {
    label: "Explore",
    items: [
      { id: "search", label: "Semantic Search", icon: Search },
      { id: "data", label: "Data Explorer", icon: Table2 },
    ],
  },
  {
    label: "Quality",
    items: [
      { id: "bias", label: "Bias & Reliability", icon: Scale },
    ],
  },
]

export function Sidebar({ activeTab, onTabChange }: { activeTab: string; onTabChange: (t: string) => void }) {
  const { sidebarOpen } = useStore()

  return (
    <aside className={cn(
      "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-[var(--color-border)] bg-[var(--color-sidebar)] transition-all duration-300",
      sidebarOpen ? "w-60" : "w-0 -translate-x-full overflow-hidden",
    )}>
      <div className="flex h-14 shrink-0 items-center gap-2.5 border-b border-[var(--color-border)] px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-primary)] text-xs font-bold text-white">
          NP
        </div>
        <span className="text-base font-semibold tracking-tight">NewsPulse</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-4 scrollbar-thin">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-5">
            <p className="mb-1.5 px-2 text-[11px] font-medium uppercase tracking-widest text-[var(--color-muted-foreground)]">
              {group.label}
            </p>
            {group.items.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-all",
                    activeTab === item.id
                      ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-medium"
                      : "text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)]",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </button>
              )
            })}
          </div>
        ))}
      </nav>
      <div className="shrink-0 border-t border-[var(--color-border)] px-4 py-3">
        <p className="text-[10px] text-[var(--color-muted-foreground)]">
          NewsPulse v2.0
        </p>
      </div>
    </aside>
  )
}
