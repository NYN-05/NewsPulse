import { create } from "zustand"
import type { Summary, ArticleRecord } from "@/types"
import { api } from "@/services/api"

interface DashboardState {
  summary: Summary | null
  articles: ArticleRecord[]
  loading: boolean
  error: string | null
  darkMode: boolean
  sidebarOpen: boolean
  lastUpdated: string | null
  filters: {
    source: string
    category: string
    days: number
    sentiment: string
  }
  setFilters: (f: Partial<DashboardState["filters"]>) => void
  toggleDark: () => void
  toggleSidebar: () => void
  fetchSummary: () => Promise<void>
  fetchArticles: (params?: Record<string, string>) => Promise<void>
}

export const useStore = create<DashboardState>((set) => ({
  summary: null,
  articles: [],
  loading: false,
  error: null,
  darkMode: true,
  sidebarOpen: true,
  lastUpdated: null,
  filters: { source: "", category: "", days: 30, sentiment: "" },

  setFilters: (f) => set((s) => ({ filters: { ...s.filters, ...f } })),

  toggleDark: () => set((s) => ({ darkMode: !s.darkMode })),

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  fetchSummary: async () => {
    set({ loading: true, error: null })
    try {
      const summary = await api.summary()
      set({ summary, loading: false, lastUpdated: new Date().toISOString() })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  fetchArticles: async (params) => {
    set({ loading: true, error: null })
    try {
      const articles = await api.data(params)
      set({ articles, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },
}))
