import { useStore } from "@/store/dashboard"
import { cn } from "@/lib/utils"
import { Sidebar } from "./sidebar"
import { Header } from "./header"

export function MainLayout({ activeTab, onTabChange, onSearchClick, children }: {
  activeTab: string
  onTabChange: (t: string) => void
  onSearchClick?: () => void
  children: React.ReactNode
}) {
  const { sidebarOpen, darkMode } = useStore()

  return (
    <div className={darkMode ? "dark" : "light"}>
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
      <div
        className={cn(
          "min-h-screen transition-all duration-300",
          sidebarOpen ? "sm:ml-60" : "ml-0",
        )}
      >
        <Header onSearchClick={onSearchClick} />
        <main className="min-h-[calc(100vh-56px)] p-4 sm:p-6">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  )
}
