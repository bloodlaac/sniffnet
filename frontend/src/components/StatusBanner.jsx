"use client";

export default function StatusBanner({ kind = "info", message }) {
  if (!message) return null;

  const color =
    kind === "error"
      ? "bg-red-50 text-red-700 border-red-200"
      : kind === "warning"
      ? "bg-yellow-50 text-yellow-700 border-yellow-200"
      : "bg-blue-50 text-blue-700 border-blue-200";

  return (
    <div className={`w-full border rounded-md px-4 py-3 ${color}`}>
      {message}
    </div>
  );
}
