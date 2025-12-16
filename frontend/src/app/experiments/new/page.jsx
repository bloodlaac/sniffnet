"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Toast from "../../components/ui/Toast";
import {
  createExperiment,
  getConfigs,
  getDatasets,
  getModels,
} from "@/lib/api";
import { getUser } from "@/lib/session";

export default function NewExperimentPage() {
  const router = useRouter();

  const [user, setUser] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [configs, setConfigs] = useState([]);
  const [models, setModels] = useState([]);
  const [form, setForm] = useState({
    dataset_id: "",
    config_id: "",
    model_id: "",
    epochs_num: "",
    batch_size: "",
    loss_function: "",
    learning_rate: "",
    optimizer: "",
    layers_num: "",
    neurons_num: "",
  });

  const [toast, setToast] = useState({ message: "", variant: "info" });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setUser(getUser());
  }, []);

  useEffect(() => {
    if (!user) return;
    const fetchDatasets = async () => {
      try {
        const [datasetsRes, configsRes, modelsRes] = await Promise.all([
          getDatasets(),
          getConfigs(),
          getModels(),
        ]);
        setDatasets(datasetsRes);
        setConfigs(configsRes);
        setModels(modelsRes);
      } catch (err) {
        setToast({
          message: err.message || "Не удалось загрузить данные для формы",
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDatasets();
  }, [user]);

  const handleConfigSelect = (configId) => {
    setForm((prev) => ({ ...prev, config_id: configId }));
    const cfg = configs.find((c) => c.config_id === Number(configId));
    if (cfg) {
      setForm((prev) => ({
        ...prev,
        epochs_num: cfg.epochs_num,
        batch_size: cfg.batch_size,
        loss_function: cfg.loss_function,
        learning_rate: cfg.learning_rate,
        optimizer: cfg.optimizer,
        layers_num: cfg.layers_num,
        neurons_num: cfg.neurons_num,
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      setToast({ message: "Авторизуйтесь, чтобы создать эксперимент", variant: "warning" });
      return;
    }
    if (!form.dataset_id) {
      setToast({ message: "Выберите датасет", variant: "warning" });
      return;
    }

    const payload = {
      user_id: user.user_id,
      dataset_id: Number(form.dataset_id),
      config: {
        epochs_num: Number(form.epochs_num),
        batch_size: Number(form.batch_size),
        loss_function: form.loss_function,
        learning_rate: Number(form.learning_rate),
        optimizer: form.optimizer,
        layers_num: Number(form.layers_num),
        neurons_num: Number(form.neurons_num),
      },
    };

    setSubmitting(true);
    setToast({ message: "", variant: "info" });
    try {
      const res = await createExperiment(payload);
      router.push(`/experiments/${res.experiment_id}`);
    } catch (err) {
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
              value={form.dataset_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, dataset_id: e.target.value }))
              }
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
                Выберите готовый вариант или заполните вручную.
              </p>
            </div>
            <Select
              value={form.config_id}
              onChange={(e) => handleConfigSelect(e.target.value)}
            >
              <option value="">Заполнить вручную</option>
              {configs.map((cfg) => (
                <option key={cfg.config_id} value={cfg.config_id}>
                  #{cfg.config_id}: epochs {cfg.epochs_num}, batch {cfg.batch_size}
                </option>
              ))}
            </Select>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Input
              label="Epochs"
              type="number"
              value={form.epochs_num}
              onChange={(e) => setForm({ ...form, epochs_num: e.target.value })}
              required
            />
            <Input
              label="Batch size"
              type="number"
              value={form.batch_size}
              onChange={(e) => setForm({ ...form, batch_size: e.target.value })}
              required
            />
            <Input
              label="Learning rate"
              type="number"
              step="0.0001"
              value={form.learning_rate}
              onChange={(e) => setForm({ ...form, learning_rate: e.target.value })}
              required
            />
            <Input
              label="Optimizer"
              value={form.optimizer}
              onChange={(e) => setForm({ ...form, optimizer: e.target.value })}
              placeholder="Adam"
              required
            />
            <Input
              label="Loss function"
              value={form.loss_function}
              onChange={(e) => setForm({ ...form, loss_function: e.target.value })}
              placeholder="crossentropy"
              required
            />
            <Input
              label="Количество слоёв"
              type="number"
              value={form.layers_num}
              onChange={(e) => setForm({ ...form, layers_num: e.target.value })}
              required
            />
            <Input
              label="Нейронов в слое"
              type="number"
              value={form.neurons_num}
              onChange={(e) => setForm({ ...form, neurons_num: e.target.value })}
              required
            />
          </div>
        </Card>

        <Card className="p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Модель</h2>
            </div>
            <Badge variant="neutral">опционально</Badge>
          </div>
          <Select
            value={form.model_id}
            onChange={(e) => setForm({ ...form, model_id: e.target.value })}
          >
            <option value="">Без выбора</option>
            {models.map((m) => (
              <option key={m.model_id} value={m.model_id}>
                {m.name || `Модель #${m.model_id}`} · конфиг {m.config_id}
              </option>
            ))}
          </Select>
        </Card>

        <div className="flex justify-end gap-3">
          <Link href="/experiments">
            <Button variant="secondary" type="button">
              Отмена
            </Button>
          </Link>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Создаём..." : "Создать эксперимент"}
          </Button>
        </div>
      </form>
    </div>
  );
}
