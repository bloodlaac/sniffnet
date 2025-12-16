"use client";

import { cn } from "@/lib/utils";

const variants = {
  success: "bg-emerald-50 text-emerald-800 border border-emerald-100",
  error: "bg-rose-50 text-rose-800 border border-rose-100",
  warning: "bg-amber-50 text-amber-800 border border-amber-100",
  info: "bg-blue-50 text-blue-800 border border-blue-100",
};

export default function Toast({ message, variant = "info", onClose }) {
  if (!message) return null;

  return (
    <div
      className={cn(
        "flex items-start justify-between rounded-xl px-4 py-3 text-sm shadow-sm",
        variants[variant]
      )}
    >
      <span>{message}</span>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="ml-4 text-xs font-semibold text-slate-500 hover:text-slate-700"
        >
          ×
        </button>
      )}
    </div>
  );
}
