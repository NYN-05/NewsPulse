import { Card, CardTitle, CardValue } from "./card"
import { cn } from "@/lib/utils"

export function MetricCard({ title, value, icon, trend, className }: {
  title: string
  value: string | number
  icon?: React.ReactNode
  trend?: { value: number; label: string }
  className?: string
}) {
  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <div className="flex items-start justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          <CardValue className="mt-1">{value}</CardValue>
        </div>
        {icon && <div className="text-[var(--color-muted-foreground)] opacity-50">{icon}</div>}
      </div>
      {trend && (
        <div className="mt-2 flex items-center gap-1 text-xs">
          <span className={trend.value >= 0 ? "text-emerald-400" : "text-red-400"}>
            {trend.value >= 0 ? "+" : ""}{trend.value}%
          </span>
          <span className="text-[var(--color-muted-foreground)]">{trend.label}</span>
        </div>
      )}
    </Card>
  )
}
