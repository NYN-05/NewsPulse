import { useStore } from "@/store/dashboard"

export function SettingsPage() {
  const { sidebarOpen, toggleSidebar } = useStore()

  return (
    <div className="animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-4 mb-6">
        <h1 className="text-lg font-medium text-[var(--color-fg)]">Settings</h1>
        <p className="text-xs text-[var(--color-fg-muted)] mt-0.5">Configuration</p>
      </div>

      <div className="space-y-4 max-w-md">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-[var(--color-fg)]">Sidebar Navigation</p>
              <p className="text-[10px] text-[var(--color-fg-muted)] font-mono mt-0.5">Toggle sidebar visibility</p>
            </div>
            <button
              onClick={toggleSidebar}
              className={`text-xs font-mono px-2.5 py-1 rounded border transition-colors ${
                sidebarOpen
                  ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                  : "border-[var(--color-border)] text-[var(--color-fg-muted)]"
              }`}
            >
              {sidebarOpen ? "visible" : "hidden"}
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
          <p className="text-sm text-[var(--color-fg)]">About</p>
          <div className="mt-2 space-y-1 text-[10px] font-mono text-[var(--color-fg-muted)]">
            <p>NewsPulse Intelligence</p>
            <p>Cross-Domain Intelligence Discovery Engine</p>
            <p>Version 2.0</p>
          </div>
        </div>
      </div>
    </div>
  )
}
