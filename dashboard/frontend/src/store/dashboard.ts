import { create } from "zustand"

interface DashboardState {
  sidebarOpen: boolean
  lastUpdated: string | null
  toggleSidebar: () => void
}

export const useStore = create<DashboardState>((set) => ({
  sidebarOpen: true,
  lastUpdated: null,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))
