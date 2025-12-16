"use client";

import { cn } from "@/lib/utils";

export function Table({ children, className }) {
  return (
    <div className={cn("overflow-hidden rounded-2xl border border-slate-200", className)}>
      <table className="min-w-full divide-y divide-slate-100 bg-white">{children}</table>
    </div>
  );
}

export function TableHead({ children }) {
  return (
    <thead className="bg-slate-50/80 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
      {children}
    </thead>
  );
}

export function TableBody({ children }) {
  return <tbody className="divide-y divide-slate-100 text-sm text-slate-800">{children}</tbody>;
}

export function TableRow({ children, className, ...props }) {
  return (
    <tr
      className={cn("transition hover:bg-slate-50", className)}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableCell({ children, className }) {
  return <td className={cn("px-4 py-3", className)}>{children}</td>;
}

export function TableHeaderCell({ children, className }) {
  return <th className={cn("px-4 py-3 font-semibold", className)}>{children}</th>;
}
