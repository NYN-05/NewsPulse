import { useStore } from "@/store/dashboard"
import { cn } from "@/lib/utils"
import { Sidebar } from "./sidebar"
import { Header } from "./header"

export function MainLayout({ activeTab, onTabChange, children }: {
  activeTab: string
  onTabChange: (t: string) => void
  children: React.ReactNode
}) {
  const { sidebarOpen } = useStore()

  return (
    <div className={cn(darkMode ? "dark" : "light")}>
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
      <div className={cn("transition-all duration-200", sidebarOpen ? "ml-56" : "ml-0")}>
        <Header />
        <main className="min-h-[calc(100vh-56px)] p-4">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  )
}

const darkMode = true
