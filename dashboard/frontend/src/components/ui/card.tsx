import { cn } from "@/lib/utils"

export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4", className)} {...props}>
      {children}
    </div>
  )
}

export function CardHeader({ className, children }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mb-3", className)}>{children}</div>
}

export function CardTitle({ className, children }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-sm font-semibold text-[var(--color-muted-foreground)] uppercase tracking-wider", className)}>{children}</h3>
}

export function CardValue({ className, children }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-3xl font-bold", className)}>{children}</p>
}
