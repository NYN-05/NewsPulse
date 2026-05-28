import { create } from "zustand"

interface DashboardState {
  loading: boolean
  error: string | null
  sidebarOpen: boolean
  lastUpdated: string | null
  toggleSidebar: () => void
}

export const useStore = create<DashboardState>((set) => ({
  loading: false,
  error: null,
  sidebarOpen: true,
  lastUpdated: null,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))
