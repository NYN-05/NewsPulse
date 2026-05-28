import { useState, useEffect, useCallback } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { HomePage } from "@/pages/home"
import { ExplorePage } from "@/pages/explore"
import { TimelinePage } from "@/pages/timeline"
import { SearchPage } from "@/pages/search"
import { SignalsPage } from "@/pages/signals"
import { SettingsPage } from "@/pages/settings"
import { api } from "@/services/api"

const pages: Record<string, React.ReactNode> = {
  home: <HomePage />,
  explore: <ExplorePage />,
  timeline: <TimelinePage />,
  search: <SearchPage />,
  signals: <SignalsPage />,
  settings: <SettingsPage />,
}

export default function App() {
  const [activeTab, setActiveTab] = useState("home")
  const [healthy, setHealthy] = useState<boolean | null>(null)

  useEffect(() => {
    api.health()
      .then((h) => setHealthy(h.status === "ok"))
      .catch(() => setHealthy(false))
  }, [])

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

  if (healthy === null) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--color-bg)]">
        <div className="text-center">
          <p className="text-sm text-[var(--color-fg-muted)] font-mono">Connecting...</p>
          <div className="mt-3 mx-auto w-4 h-4 border border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (healthy === false) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-[var(--color-bg)] text-[var(--color-fg-secondary)] px-4">
        <p className="text-sm font-mono">Backend unavailable</p>
        <code className="text-[10px] font-mono text-[var(--color-fg-muted)] bg-[var(--color-card)] border border-[var(--color-border)] rounded px-2 py-1">
          python dashboard/backend/main.py
        </code>
        <button
          onClick={() => {
            setHealthy(null)
            api.health().then((h) => setHealthy(h.status === "ok")).catch(() => setHealthy(false))
          }}
          className="text-xs text-[var(--color-accent)] hover:underline font-mono mt-2"
        >
          retry
        </button>
      </div>
    )
  }

  return (
    <MainLayout activeTab={activeTab} onTabChange={setActiveTab} onSearchClick={handleSearchClick}>
      {pages[activeTab] || <HomePage />}
    </MainLayout>
  )
}
