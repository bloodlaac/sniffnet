"use client";

import { useEffect, useState } from "react";
import ImageUploader from "@/components/ImageUploader";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Toast from "../components/ui/Toast";
import Badge from "../components/ui/Badge";
import Select from "../components/ui/Select";
import { getModels, predict } from "@/lib/api";

const classesMapping = {
  "Bad": "Испорченный",
  "Fresh": "Свежий",
}

export default function PredictPage() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState({ message: "", variant: "info" });
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [modelsLoading, setModelsLoading] = useState(true);

  useEffect(() => {
    const loadModels = async () => {
      setModelsLoading(true);
      try {
        const data = await getModels();
        setModels(Array.isArray(data) ? data : data?.items || []);
      } catch (err) {
        setToast({
          message: err.message || "Не удалось загрузить список моделей",
          variant: "error",
        });
      } finally {
        setModelsLoading(false);
      }
    };

    loadModels();
  }, []);

  const handlePredict = async () => {
    if (!file) {
      setToast({ message: "Выберите изображение для проверки", variant: "warning" });
      return;
    }
    if (!selectedModel) {
      setToast({ message: "Выберите модель для инференса", variant: "warning" });
      return;
    }

    setLoading(true);
    setResult(null);
    setToast({ message: "Отправляем изображение в модель...", variant: "info" });

    try {
      const data = await predict(file, selectedModel);
      setResult(data);
      setToast({ message: "Прогноз готов", variant: "success" });
    } catch (err) {
      setToast({ message: err.message || "Не удалось получить предсказание", variant: "error" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Проверка за секунду</h1>
          <p className="text-sm text-slate-600 mt-2">
            Загрузите изображение продукта и узнайте его степерь свежести
          </p>
        </div>
      </div>

      {toast.message && (
        <Toast
          message={toast.message}
          variant={toast.variant}
          onClose={() => setToast({ message: "", variant: "info" })}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900">Загрузка изображения</h2>
            <Badge variant="info">JPEG/PNG</Badge>
          </div>
          <div className="space-y-2">
            <p className="text-sm font-semibold text-slate-800">Выбор модели</p>
            {modelsLoading ? (
              <p className="text-sm text-slate-600">Загружаем список моделей...</p>
            ) : models.length === 0 ? (
              <p className="text-sm text-slate-600">
                Нет обученных моделей, сначала обучите модель.
              </p>
            ) : (
              <Select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                <option value="">Выберите модель</option>
                {models.map((model) => (
                <option key={model.model_id} value={model.model_id}>
                    {`model${model.model_id}`}
                </option>
                ))}
              </Select>
            )}
          </div>
          <ImageUploader
            valueFile={file}
            onChange={setFile}
            disabled={loading || !selectedModel}
          />
          <div className="flex justify-end">
            <Button
              onClick={handlePredict}
              disabled={loading || modelsLoading || models.length === 0 || !selectedModel}
            >
              {loading ? "Отправляем..." : "Получить прогноз"}
            </Button>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900">Результат</h2>
            {result && (
              <Badge variant="success">
                {result.confidence !== undefined
                  ? `${Math.round(result.confidence * 100)}% уверенности`
                  : "Результат готов"}
              </Badge>
            )}
          </div>

          {result && (
            <div className="space-y-3">
              <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                <p className="text-2xl font-semibold text-slate-900">{classesMapping[result.class]}</p>
                <p className="text-sm text-slate-600">
                  Вероятность:{" "}
                  {Math.round(result.confidence * 100)}%
                </p>
              </div>
              {result.probs && (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-800">Процент уверенности по классам</p>
                  <div className="space-y-2">
                    {Object.entries(result.probs).map(([label, value]) => (
                      <div
                        key={label}
                        className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2"
                      >
                        <span className="text-sm text-slate-700">{classesMapping[label]}</span>
                        <span className="font-mono text-sm text-slate-900">
                          {(value * 100).toFixed(2)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
