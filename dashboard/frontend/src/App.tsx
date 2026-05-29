import { useState, useEffect, useCallback, useRef } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { HomePage } from "@/pages/home"
import { ExplorePage } from "@/pages/explore"
import { TimelinePage } from "@/pages/timeline"
import { SearchPage } from "@/pages/search"
import { SignalsPage } from "@/pages/signals"
import { api } from "@/services/api"
import { useStore } from "@/store/dashboard"

const pages: Record<string, React.ReactNode> = {
  home: <HomePage />,
  explore: <ExplorePage />,
  timeline: <TimelinePage />,
  search: <SearchPage />,
  signals: <SignalsPage />,
}

const POLL_INTERVAL = 30000

export default function App() {
  const [activeTab, setActiveTab] = useState("home")
  const [healthy, setHealthy] = useState<boolean | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const handleSearchClick = useCallback(() => setActiveTab("search"), [])

  useEffect(() => {
    const check = () => {
      api.health()
        .then((h) => {
          setHealthy(true)
          if (h.pipeline) useStore.getState().setPipeline(h.pipeline)
        })
        .catch(() => setHealthy(false))
    }
    check()
    pollRef.current = setInterval(check, POLL_INTERVAL)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); setActiveTab("search") }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  if (healthy === null) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--color-bg)]">
        <div className="text-center">
          <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Connecting...</p>
          <div className="mt-4 mx-auto w-4 h-4 border border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (healthy === false) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-[var(--color-bg)] px-4">
        <p className="text-sm font-serif text-[var(--color-fg)]">Backend unavailable</p>
        <code className="text-[10px] font-mono text-[var(--color-fg-muted)] bg-[var(--color-card)] border border-[var(--color-border)] rounded px-2 py-1">
          python dashboard/backend/main.py
        </code>
        <button
          onClick={() => {
            setHealthy(null)
            api.health().then((h) => { setHealthy(true); if (h.pipeline) useStore.getState().setPipeline(h.pipeline) }).catch(() => setHealthy(false))
          }}
          className="text-[10px] font-mono text-[var(--color-accent)] hover:underline mt-2 tracking-wider"
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
