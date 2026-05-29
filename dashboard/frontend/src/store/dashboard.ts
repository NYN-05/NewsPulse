import { create } from "zustand"

export interface PipelineStatus {
  status: string
  last_run_at: string | null
  last_run_duration: number | null
  last_run_success: boolean | null
  last_error: string | null
  next_run_at: string | null
  run_count: number
  articles_analyzed: number
}

interface DashboardState {
  sidebarOpen: boolean
  lastUpdated: string | null
  pipeline: PipelineStatus | null
  toggleSidebar: () => void
  setPipeline: (p: PipelineStatus) => void
}

export const useStore = create<DashboardState>((set) => ({
  sidebarOpen: true,
  lastUpdated: null,
  pipeline: null,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setPipeline: (p) => set({ pipeline: p, lastUpdated: p.last_run_at || new Date().toISOString() }),
}))
