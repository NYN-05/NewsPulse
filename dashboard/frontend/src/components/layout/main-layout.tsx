import { useStore } from "@/store/dashboard"
import { Sidebar } from "./sidebar"
import { Header } from "./header"

export function MainLayout({ activeTab, onTabChange, onSearchClick, children }: {
  activeTab: string
  onTabChange: (t: string) => void
  onSearchClick?: () => void
  children: React.ReactNode
}) {
  const open = useStore((s) => s.sidebarOpen)

  return (
    <div>
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
      <div className={`min-h-screen transition-all duration-200 ${open ? "sm:ml-52" : "ml-0"}`}>
        <Header onSearchClick={onSearchClick} />
        <main className="min-h-[calc(100vh-48px)] px-6 py-8">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  )
}
