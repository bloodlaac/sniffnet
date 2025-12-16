"use client";

import { useEffect, useState } from "react";
import ImageUploader from "../components/ImageUploader";
import PredictionResult from "../components/PredictionResult";
import StatusBanner from "../components/StatusBanner";
import { prewarmModel, predictWithRetry } from "../lib/api";

export default function Home() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [warningMessage, setWarningMessage] = useState(null);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const warmUp = async () => {
      setStatusMessage("Прогрев модели...");
      try {
        await prewarmModel();
        if (!cancelled) {
          setStatusMessage("Модель готовится...");
        }
      } catch (err) {
        if (!cancelled) {
          setWarningMessage(err.message || "Не удалось прогреть модель");
          setStatusMessage(null);
        }
      }
    };

    warmUp();

    return () => {
      cancelled = true;
    };
  }, []);

  const handlePredict = async () => {
    if (!selectedFile) {
      setErrorMessage("Выберите изображение для проверки");
      return;
    }

    const maxRetries = 5;
    setErrorMessage(null);
    setWarningMessage(null);
    setResult(null);
    setSubmitting(true);
    setStatusMessage("Отправляем изображение...");

    try {
      const prediction = await predictWithRetry(selectedFile, {
        retries: maxRetries,
        delayMs: 1200,
        onRetry: (attempt) => {
          setStatusMessage(`Модель загружается, пробуем снова (${attempt}/${maxRetries})...`);
        },
      });
      setResult(prediction);
      setStatusMessage("Готово");
    } catch (err) {
      setErrorMessage(err.message || "Ошибка при предсказании");
      setStatusMessage(null);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <header className="mb-10">
          <h1 className="text-3xl font-bold mb-2">Проверка свежести</h1>
          <p className="text-gray-700">
            Загрузите фото продукта, чтобы модель определила его состояние.
          </p>
        </header>

        <div className="space-y-4">
          {statusMessage && <StatusBanner kind="info" message={statusMessage} />}
          {warningMessage && <StatusBanner kind="warning" message={warningMessage} />}
          {errorMessage && <StatusBanner kind="error" message={errorMessage} />}
        </div>

        <div className="mt-6 space-y-6">
          <ImageUploader valueFile={selectedFile} onChange={setSelectedFile} disabled={submitting} />

          <div className="flex justify-end">
            <button
              type="button"
              onClick={handlePredict}
              disabled={submitting}
              className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
                submitting ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {submitting ? "Проверяем..." : "Проверить"}
            </button>
          </div>

          <PredictionResult result={result} />
        </div>
      </div>
    </div>
  );
}
