"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

const Select = forwardRef(function Select(
  { label, error, className, children, ...props },
  ref
) {
  return (
    <label className="flex flex-col gap-2 text-sm text-slate-700">
      {label && <span className="font-semibold text-slate-800">{label}</span>}
      <select
        ref={ref}
        className={cn(
          "w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-slate-900 shadow-inner shadow-slate-100 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100",
          error && "border-rose-300 focus:ring-rose-100",
          className
        )}
        {...props}
      >
        {children}
      </select>
      {error && <span className="text-xs text-rose-600">{error}</span>}
    </label>
  );
});

export default Select;
