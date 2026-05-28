import { cn } from "@/lib/utils"

const variants: Record<string, string> = {
  default: "bg-[var(--color-muted)] text-[var(--color-foreground)]",
  positive: "bg-emerald-500/20 text-emerald-400",
  negative: "bg-red-500/20 text-red-400",
  neutral: "bg-gray-500/20 text-gray-400",
  primary: "bg-[var(--color-primary)] text-white",
  warning: "bg-amber-500/20 text-amber-400",
  info: "bg-cyan-500/20 text-cyan-400",
}

export function Badge({ variant = "default", className, children }: { variant?: string; className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", variants[variant] || variants.default, className)}>
      {children}
    </span>
  )
}
