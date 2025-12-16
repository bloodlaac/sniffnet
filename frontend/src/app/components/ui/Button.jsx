"use client";

import { cn } from "@/lib/utils";

const variants = {
  primary:
    "bg-blue-600 text-white shadow-md shadow-blue-200 hover:bg-blue-700 active:bg-blue-800",
  secondary:
    "bg-white text-blue-700 border border-blue-100 hover:border-blue-200 hover:bg-blue-50",
  ghost:
    "bg-transparent text-slate-700 hover:bg-slate-100 border border-transparent",
};

const sizes = {
  sm: "text-sm px-3 py-2",
  md: "text-sm px-4 py-2.5",
  lg: "text-base px-5 py-3",
};

export default function Button({
  className,
  variant = "primary",
  size = "md",
  disabled,
  children,
  ...props
}) {
  return (
    <button
      className={cn(
        "rounded-xl font-semibold transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-200",
        variants[variant],
        sizes[size],
        disabled && "opacity-60 cursor-not-allowed shadow-none",
        className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
