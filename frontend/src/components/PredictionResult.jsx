"use client";

export default function PredictionResult({ result }) {
  if (!result) return null;

  const { class: predictedClass, confidence, probs } = result;

  return (
    <div className="w-full bg-white border rounded-lg p-6 shadow-sm mt-6">
      <h3 className="text-xl font-bold mb-2">Результат</h3>
      <p className="text-2xl font-semibold mb-1">
        {predictedClass} ({Math.round(confidence * 100)}%)
      </p>
      <div className="mt-3">
        <h4 className="font-semibold mb-1">Вероятности</h4>
        <ul className="space-y-1">
          {probs &&
            Object.entries(probs).map(([label, value]) => (
              <li key={label} className="flex justify-between bg-gray-50 px-3 py-2 rounded">
                <span>{label}</span>
                <span className="font-mono">{(value * 100).toFixed(2)}%</span>
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}
