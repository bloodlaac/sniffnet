"use client";

import { cn } from "@/lib/utils";

export default function Card({ className, children }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200 bg-white/90 shadow-[0_12px_30px_rgba(15,23,42,0.06)]",
        className
      )}
    >
      {children}
    </div>
  );
}
