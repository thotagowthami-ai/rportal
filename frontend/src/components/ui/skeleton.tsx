import { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

/**
 * A beautiful, shimmering skeleton loader component.
 * Use this to indicate loading states for cards, text rows, and tables.
 */
export function Skeleton({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-[#e8dfd6]/50 shadow-inner overflow-hidden relative",
        // Adding a subtle shimmer effect
        "after:absolute after:inset-0 after:-translate-x-full after:animate-[shimmer_2s_infinite] after:bg-gradient-to-r after:from-transparent after:via-white/20 after:to-transparent",
        className
      )}
      {...props}
    />
  );
}

export function SkeletonRow({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex gap-4 py-4 px-8 border-b border-[#e8dfd6]">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className="h-6 flex-1" />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl p-5 border border-[#e8dfd6] space-y-3">
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-10 w-3/4" />
      <Skeleton className="h-4 w-1/4" />
    </div>
  );
}
