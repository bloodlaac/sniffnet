"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Toast from "../../components/ui/Toast";
import {
  getDatasets,
  startExperiment,
} from "@/lib/api";
import { getUser } from "@/lib/session";
import {
  DEFAULT_TRAINING_CONFIG,
  TRAINING_LOSS_FUNCTIONS,
  TRAINING_OPTIMIZERS,
  VALIDATION_SPLITS,
} from "@/constants/trainingOptions";

const buildDefaultForm = () => ({
  dataset_id: "",
  ...DEFAULT_TRAINING_CONFIG,
});

const parseNumber = (value) => {
  const num = Number(value);
  return Number.isFinite(num) ? num : NaN;
};

export default function NewExperimentPage() {
  const router = useRouter();

  const [user, setUser] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [form, setForm] = useState(buildDefaultForm());

  const [toast, setToast] = useState({ message: "", variant: "info" });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [submitError, setSubmitError] = useState("");

  useEffect(() => {
    setUser(getUser());
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const datasetsRes = await getDatasets();
        const list = Array.isArray(datasetsRes)
          ? datasetsRes
          : datasetsRes?.items || [];
        setDatasets(list);
      } catch (err) {
        console.debug("Datasets fetch failed", {
          url: err.url,
          status: err.status,
          data: err.data,
        });
        setToast({
          message: "Не удалось загрузить датасеты",
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const errors = useMemo(() => {
    const nextErrors = {};
    if (!form.dataset_id) {
      nextErrors.dataset_id = "Выберите датасет";
    }

    const epochs = parseNumber(form.epochs_num);
    if (!Number.isFinite(epochs) || epochs < 1) {
      nextErrors.epochs_num = "Минимум 1 эпоха";
    }

    const batchSize = parseNumber(form.batch_size);
    if (!Number.isFinite(batchSize) || batchSize < 1) {
      nextErrors.batch_size = "Минимум 1";
    }

    const learningRate = parseNumber(form.learning_rate);
    if (!Number.isFinite(learningRate) || learningRate <= 0 || learningRate > 1) {
      nextErrors.learning_rate = "Значение от 0 до 1";
    }

    if (!TRAINING_OPTIMIZERS.includes(form.optimizer)) {
      nextErrors.optimizer = "Выберите оптимизатор из списка";
    }

    if (!TRAINING_LOSS_FUNCTIONS.includes(form.loss_function)) {
      nextErrors.loss_function = "Выберите функцию потерь";
    }

    if (
      typeof form.val_split !== "number" ||
      form.val_split <= 0 ||
      form.val_split >= 1
    ) {
      nextErrors.val_split = "Выберите долю валидации";
    }

    return nextErrors;
  }, [form]);

  const canSubmit =
    Object.keys(errors).length === 0 && !submitting && !loading && Boolean(user);

  const handleReset = () => {
    setForm((prev) => ({
      ...prev,
      ...DEFAULT_TRAINING_CONFIG,
    }));
    setShowErrors(false);
    setSubmitError("");
    setToast({ message: "", variant: "info" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      setToast({
        message: "Авторизуйтесь, чтобы создать эксперимент",
        variant: "warning",
      });
      return;
    }

    setShowErrors(true);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSubmitting(true);
    setSubmitError("");
    setToast({ message: "", variant: "info" });
    try {
      const experimentRes = await startExperiment({
        user_id: user.user_id,
        dataset_id: Number(form.dataset_id),
        config: {
          epochs_num: Number(form.epochs_num),
          batch_size: Number(form.batch_size),
          loss_function: form.loss_function,
          learning_rate: Number(form.learning_rate),
          optimizer: form.optimizer,
          val_split: form.val_split,
        },
      });
      router.push(`/experiments/${experimentRes.experiment_id}`);
    } catch (err) {
      setSubmitError(err.message || "Ошибка при создании эксперимента");
      setToast({
        message: err.message || "Ошибка при создании эксперимента",
        variant: "error",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Конфигурация
          </h1>
          <p className="text-sm text-slate-600">
            Выберите датасет, заполните конфигурацию или возьмите готовую.
          </p>
        </div>
        <Link href="/experiments">
          <Button variant="secondary">Вернуться к списку</Button>
        </Link>
      </div>

      {toast.message && (
        <Toast
          message={toast.message}
          variant={toast.variant}
          onClose={() => setToast({ message: "", variant: "info" })}
        />
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Датасет</h2>
            <Badge variant="info">Обязательное поле</Badge>
          </div>
          {loading ? (
            <p className="text-sm text-slate-600">Загружаем списки...</p>
          ) : (
            <Select
              label="Выбор датасета"
              value={form.dataset_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, dataset_id: e.target.value }))
              }
              error={showErrors ? errors.dataset_id : ""}
            >
              <option value="">-</option>
              {datasets.map((d) => (
                <option key={d.dataset_id} value={d.dataset_id}>
                  {d.name} (классов: {d.classes_num})
                </option>
              ))}
            </Select>
          )}
        </Card>

        <Card className="p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Конфигурация обучения
              </h2>
              <p className="text-sm text-slate-600">
                Укажите параметры обучения для эксперимента.
              </p>
            </div>
            <Button variant="secondary" type="button" onClick={handleReset}>
              Сброс
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Input
              label="Epochs"
              type="number"
              value={form.epochs_num}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, epochs_num: e.target.value }))
              }
              error={showErrors ? errors.epochs_num : ""}
              required
            />
            <Input
              label="Batch size"
              type="number"
              value={form.batch_size}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, batch_size: e.target.value }))
              }
              error={showErrors ? errors.batch_size : ""}
              required
            />
            <Input
              label="Learning rate"
              type="number"
              step="0.0001"
              value={form.learning_rate}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, learning_rate: e.target.value }))
              }
              error={showErrors ? errors.learning_rate : ""}
              required
            />
            <Select
              label="Optimizer"
              value={form.optimizer}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, optimizer: e.target.value }))
              }
              error={showErrors ? errors.optimizer : ""}
              required
            >
              {TRAINING_OPTIMIZERS.map((optimizer) => (
                <option key={optimizer} value={optimizer}>
                  {optimizer}
                </option>
              ))}
            </Select>
            <Select
              label="Loss function"
              value={form.loss_function}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, loss_function: e.target.value }))
              }
              error={showErrors ? errors.loss_function : ""}
              required
            >
              {TRAINING_LOSS_FUNCTIONS.map((loss) => (
                <option key={loss} value={loss}>
                  {loss}
                </option>
              ))}
            </Select>
            <Select
              label="Размер валидационной выборки"
              value={String(form.val_split)}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, val_split: Number(e.target.value) }))
              }
              error={showErrors ? errors.val_split : ""}
              required
            >
              {VALIDATION_SPLITS.map((split) => (
                <option key={split.value} value={split.value}>
                  {split.label}
                </option>
              ))}
            </Select>
          </div>
        </Card>

        <div className="flex flex-wrap justify-end gap-3">
          <Link href="/experiments">
            <Button variant="secondary" type="button">
              Отмена
            </Button>
          </Link>
          <Button type="submit" disabled={!canSubmit}>
            {submitting ? "Создаём..." : "Создать эксперимент"}
          </Button>
        </div>
        {submitError && (
          <p className="text-sm text-rose-600 text-right">{submitError}</p>
        )}
      </form>
    </div>
  );
}
