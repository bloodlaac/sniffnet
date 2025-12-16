"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Toast from "../../components/ui/Toast";
import { getDatasets, getExperiment } from "@/lib/api";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const formatDateTime = (value) => {
  if (!value) return "—";
  return new Date(value).toLocaleString("ru-RU");
};

export default function ExperimentDetails({ params }) {
  const [experiment, setExperiment] = useState(null);
  const [datasetName, setDatasetName] = useState("");
  const [toast, setToast] = useState({ message: "", variant: "info" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [expData, datasets] = await Promise.all([
          getExperiment(params.id),
          getDatasets(),
        ]);
        setExperiment(expData);
        const ds = datasets.find((d) => d.dataset_id === expData.dataset_id);
        setDatasetName(ds?.name || `Датасет ${expData.dataset_id}`);
      } catch (err) {
        setToast({
          message: err.message || "Не удалось загрузить эксперимент",
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [params.id]);

  const status = useMemo(() => {
    if (!experiment) return { label: "—", variant: "neutral" };
    return experiment.end_time
      ? { label: "Завершён", variant: "success" }
      : { label: "В процессе", variant: "warning" };
  }, [experiment]);

  const accuracyHistory =
    experiment?.accuracy_history || experiment?.train_accuracy_history;
  const lossHistory = experiment?.loss_history || experiment?.train_loss_history;

  const hasSeries =
    (Array.isArray(accuracyHistory) && accuracyHistory.length > 1) ||
    (Array.isArray(lossHistory) && lossHistory.length > 1);

  const chartData = useMemo(() => {
    const labels =
      (accuracyHistory || lossHistory || []).map((_, idx) => `Эпоха ${idx + 1}`);
    const datasets = [];

    if (Array.isArray(accuracyHistory) && accuracyHistory.length) {
      datasets.push({
        label: "Accuracy",
        data: accuracyHistory,
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.15)",
        tension: 0.3,
      });
    }
    if (Array.isArray(lossHistory) && lossHistory.length) {
      datasets.push({
        label: "Loss",
        data: lossHistory,
        borderColor: "rgb(239, 68, 68)",
        backgroundColor: "rgba(239, 68, 68, 0.12)",
        tension: 0.3,
      });
    }
    return { labels, datasets };
  }, [accuracyHistory, lossHistory]);

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-600">
        Загружаем детали эксперимента...
      </div>
    );
  }

  if (!experiment) {
    return (
      <div className="space-y-4">
        {toast.message && (
          <Toast
            message={toast.message}
            variant={toast.variant}
            onClose={() => setToast({ message: "", variant: "info" })}
          />
        )}
        <Card className="p-6">
          <p className="text-slate-700">Эксперимент не найден.</p>
          <div className="mt-4">
            <Link href="/experiments">
              <Button variant="secondary">Вернуться к списку</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide text-blue-600">
            Эксперимент #{experiment.experiment_id}
          </p>
          <h1 className="text-3xl font-bold text-slate-900">{datasetName}</h1>
          <p className="text-sm text-slate-600">
            Пользователь: {experiment.user_id}. Конфигурация {experiment.config_id}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={status.variant}>{status.label}</Badge>
          <Link href="/experiments">
            <Button variant="secondary" size="sm">
              К списку
            </Button>
          </Link>
        </div>
      </div>

      {toast.message && (
        <Toast
          message={toast.message}
          variant={toast.variant}
          onClose={() => setToast({ message: "", variant: "info" })}
        />
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Общая информация
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
              <p className="text-xs uppercase text-slate-500">Датасет</p>
              <p className="text-base font-semibold text-slate-900">
                {datasetName}
              </p>
              <p className="text-xs text-slate-500">
                id: {experiment.dataset_id}
              </p>
            </div>
            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
              <p className="text-xs uppercase text-slate-500">Период</p>
              <p className="text-base font-semibold text-slate-900">
                {formatDateTime(experiment.start_time)}
              </p>
              <p className="text-xs text-slate-500">
                Завершение: {formatDateTime(experiment.end_time)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-semibold text-slate-900 mb-3">
            Результаты
          </h2>
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-100 bg-white px-4 py-3">
              <p className="text-xs uppercase text-slate-500">Train accuracy</p>
              <p className="text-2xl font-semibold text-slate-900">
                {experiment.train_accuracy !== null
                  ? `${Math.round(experiment.train_accuracy * 100) / 100}`
                  : "нет данных"}
              </p>
            </div>
            <div className="rounded-xl border border-slate-100 bg-white px-4 py-3">
              <p className="text-xs uppercase text-slate-500">Train loss</p>
              <p className="text-2xl font-semibold text-slate-900">
                {experiment.train_loss !== null
                  ? `${Math.round(experiment.train_loss * 1000) / 1000}`
                  : "нет данных"}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-slate-900">
            Конфигурация обучения
          </h2>
          <Badge variant="info">config #{experiment.config_id}</Badge>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <InfoCell label="Epochs" value={experiment.epochs_num} />
          <InfoCell label="Batch size" value={experiment.batch_size} />
          <InfoCell label="Learning rate" value={experiment.learning_rate} />
          <InfoCell label="Optimizer" value={experiment.optimizer} />
          <InfoCell label="Loss function" value={experiment.loss_function} />
          <InfoCell label="Layers" value={experiment.layers_num} />
          <InfoCell label="Neurons" value={experiment.neurons_num} />
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">
              Графики обучения
            </h2>
            <Badge variant={hasSeries ? "info" : "neutral"}>
              {hasSeries ? "по эпохам" : "нет данных по эпохам"}
            </Badge>
          </div>
          <div className="mt-4 min-h-[260px]">
            {hasSeries ? (
              <Line
                data={chartData}
                options={{
                  responsive: true,
                  plugins: {
                    legend: { position: "bottom" },
                  },
                }}
              />
            ) : (
              <div className="flex h-full min-h-[240px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-600">
                Backend пока отдаёт только финальные значения. Добавьте историю по эпохам, чтобы увидеть график.
              </div>
            )}
          </div>
        </Card>

        <Card className="p-5 space-y-3">
          <h2 className="text-lg font-semibold text-slate-900">Данные графиков</h2>
          <p className="text-sm text-slate-600">
            Сейчас backend возвращает финальные показатели train_accuracy и train_loss. Когда появятся значения по эпохам,
            они автоматически отобразятся на графике выше.
          </p>
          <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase text-slate-500">Финальные значения</p>
            <ul className="mt-2 space-y-1 text-sm text-slate-700">
              <li>Accuracy: {experiment.train_accuracy ?? "нет"}</li>
              <li>Loss: {experiment.train_loss ?? "нет"}</li>
            </ul>
          </div>
          <p className="text-xs text-slate-500">
            Поддерживаются массивы accuracy_history и loss_history, чтобы строить кривые обучения.
          </p>
        </Card>
      </div>
    </div>
  );
}

function InfoCell({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white px-4 py-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="text-base font-semibold text-slate-900">
        {value !== null && value !== undefined ? value : "—"}
      </p>
    </div>
  );
}
