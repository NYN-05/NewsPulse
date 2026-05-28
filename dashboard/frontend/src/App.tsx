import { useState, useEffect, useCallback } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { LoadingPage } from "@/components/ui/loading"
import { OverviewPage } from "@/pages/overview"
import { SentimentPage } from "@/pages/sentiment"
import { CategoriesPage } from "@/pages/categories"
import { ClustersPage } from "@/pages/clusters"
import { TrendsPage } from "@/pages/trends"
import { EntityGraphPage } from "@/pages/entity-graph"
import { EntityTrendsPage } from "@/pages/entity-trends"
import { BreakingPage } from "@/pages/breaking"
import { ViralityPage } from "@/pages/virality"
import { BiasPage } from "@/pages/bias"
import { EvolutionPage } from "@/pages/evolution"
import { SearchPage } from "@/pages/search"
import { DataExplorerPage } from "@/pages/data-explorer"
import { CrossDomainPage } from "@/pages/cross-domain"
import { NarrativesPage } from "@/pages/narratives"
import { InfluencePage } from "@/pages/influence"
import { api } from "@/services/api"
import { useStore } from "@/store/dashboard"

const pages: Record<string, React.ReactNode> = {
  overview: <OverviewPage />,
  sentiment: <SentimentPage />,
  categories: <CategoriesPage />,
  clusters: <ClustersPage />,
  trends: <TrendsPage />,
  "entity-graph": <EntityGraphPage />,
  "cross-domain": <CrossDomainPage />,
  narratives: <NarrativesPage />,
  influence: <InfluencePage />,
  "entity-trends": <EntityTrendsPage />,
  breaking: <BreakingPage />,
  virality: <ViralityPage />,
  bias: <BiasPage />,
  evolution: <EvolutionPage />,
  search: <SearchPage />,
  data: <DataExplorerPage />,
}

export default function App() {
  const [activeTab, setActiveTab] = useState("overview")
  const [healthy, setHealthy] = useState<boolean | null>(null)
  const { fetchSummary } = useStore()

  useEffect(() => {
    api.health()
      .then((h) => {
        setHealthy(h.status === "ok")
        if (h.status === "ok") fetchSummary()
      })
      .catch(() => setHealthy(false))
  }, [fetchSummary])

  const handleSearchClick = useCallback(() => {
    setActiveTab("search")
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault()
        setActiveTab("search")
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  if (healthy === null) return <LoadingPage />

  if (healthy === false) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-[var(--color-background)] text-[var(--color-foreground)] p-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10">
          <span className="text-2xl">📡</span>
        </div>
        <h1 className="text-xl font-bold">Backend Unavailable</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] text-center max-w-md">
          The NewsPulse API server is not running. Start it with:
        </p>
        <code className="rounded-lg bg-[var(--color-muted)] px-3 py-2 text-xs font-mono">
          python dashboard/backend/main.py
        </code>
        <button
          onClick={() => {
            setHealthy(null)
            api.health().then((h) => setHealthy(h.status === "ok")).catch(() => setHealthy(false))
          }}
          className="mt-2 rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition-opacity"
        >
          Retry Connection
        </button>
      </div>
    )
  }

  return (
    <MainLayout activeTab={activeTab} onTabChange={setActiveTab} onSearchClick={handleSearchClick}>
      {pages[activeTab] || <OverviewPage />}
    </MainLayout>
  )
}
