"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Toast from "../../components/ui/Toast";
import { getDatasets, getExperiment } from "@/lib/api";

const formatDateTime = (value) => {
  if (!value) return "—";
  return new Date(value).toLocaleString("ru-RU");
};

const formatPercent = (value) => {
  if (typeof value !== "number") return "—";
  return `${Math.round(value * 100)}%`;
};

export default function ExperimentDetails() {
  const routeParams = useParams();
  const rawId = routeParams?.id;
  const experimentId = Array.isArray(rawId) ? rawId[0] : rawId;
  const [experiment, setExperiment] = useState(null);
  const [datasetName, setDatasetName] = useState("");
  const [toast, setToast] = useState({ message: "", variant: "info" });
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const normalizeError = (err) => {
    if (!err) return "Неизвестная ошибка";
    if (typeof err === "string") return err;
    if (err instanceof Error) return err.message;
    if (typeof err === "object") {
      if (typeof err.detail === "string") return err.detail;
      if (typeof err.message === "string") return err.message;
      try {
        return JSON.stringify(err);
      } catch {
        return "Ошибка";
      }
    }
    return String(err);
  };

  useEffect(() => {
    if (!experimentId) return;
    let intervalId;
    const load = async () => {
      setLoading(true);
      try {
        const [expData, datasets] = await Promise.all([
          getExperiment(experimentId),
          getDatasets(),
        ]);
        setExperiment(expData);
        const ds = datasets.find((d) => d.dataset_id === expData.dataset_id);
        setDatasetName(ds?.name || `Датасет ${expData.dataset_id}`);
        setErrorMessage("");
      } catch (err) {
        const message = normalizeError(err);
        setErrorMessage(message);
        setToast({ message, variant: "error" });
      } finally {
        setLoading(false);
      }
    };

    const poll = async () => {
      try {
        const expData = await getExperiment(experimentId);
        setExperiment(expData);
        setErrorMessage("");
      } catch (err) {
        const message = normalizeError(err);
        setErrorMessage(message);
        setToast({ message, variant: "error" });
      }
    };

    load();
    intervalId = setInterval(() => {
      if (experiment?.status === "queued" || experiment?.status === "running") {
        poll();
      }
    }, 5000);

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [experimentId, experiment?.status]);

  const status = useMemo(() => {
    if (!experiment) return { label: "—", variant: "neutral" };
    switch (experiment.status) {
      case "queued":
        return { label: "В очереди", variant: "warning" };
      case "running":
        return { label: "В процессе", variant: "warning" };
      case "failed":
        return { label: "Ошибка", variant: "error" };
      case "success":
        return { label: "Завершён", variant: "success" };
      default:
        return experiment.end_time
          ? { label: "Завершён", variant: "success" }
          : { label: "В процессе", variant: "warning" };
    }
  }, [experiment]);

  const canShowReport = experiment?.status === "success";

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
          <p className="text-slate-700">
            {errorMessage || "Эксперимент не найден."}
          </p>
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
            Пользователь: {experiment.user_id ?? "—"}. Конфигурация {experiment.config_id}.
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
          <InfoCell
            label="Validation split"
            value={formatPercent(experiment.val_split)}
          />
          <InfoCell label="Model ID" value={experiment.model_id ?? "—"} />
        </div>
      </Card>
      {experiment.error_message && (
        <Card className="p-5">
          <p className="text-sm text-rose-600">
            Ошибка обучения: {experiment.error_message}
          </p>
        </Card>
      )}

      <Card className="p-5 space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">Отчёт эксперимента</h2>
        {!canShowReport && (
          <p className="text-sm text-slate-600">
            Отчёт будет доступен после завершения обучения.
          </p>
        )}
        {canShowReport && (
          <img
            alt={`Отчёт эксперимента ${experiment.experiment_id}`}
            src={`/api/experiments/${experiment.experiment_id}/report`}
            className="w-full rounded-xl border border-slate-200"
          />
        )}
      </Card>
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
