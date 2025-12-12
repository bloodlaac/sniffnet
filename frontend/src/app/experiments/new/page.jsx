"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/apiFetch";

export default function NewExperimentPage() {
  const router = useRouter();

  const [datasets, setDatasets] = useState([]);
  const [form, setForm] = useState({
    dataset_id: '',
    user_id: null,
    start_time: '',
    end_time: '',
    epochs_num: '',
    batch_size: '',
    loss_function: '',
    learning_rate: '',
    optimizer: '',
    layers_num: '',
    neurons_num: '',
  });

  const [error, setError] = useState("");

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (userId) {
      setForm((prev) => ({ ...prev, user_id: Number(userId) }));
    } else {
      setError("Пользователь не найден. Войдите в систему.");
    }
  }, []);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const data = await apiFetch("/datasets");
        setDatasets(data);
      } catch (err) {
        setError("Ошибка загрузки датасетов");
        console.error(err);
      }
    };

    fetchDatasets();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!form.user_id) {
      setError("Пользователь не авторизован.");
      return;
    }

    const payload = {
      user_id: form.user_id,
      dataset_id: form.dataset_id,
      config: {
        epochs_num: form.epochs_num,
        batch_size: form.batch_size,
        loss_function: form.loss_function,
        learning_rate: form.learning_rate,
        optimizer: form.optimizer,
        layers_num: form.layers_num,
        neurons_num: form.neurons_num,
      },
    };

    try {
      await apiFetch("/experiments", {
        method: "POST",
        body: payload,
      });
      router.push("/experiments");
    } catch (err) {
      console.error("Ошибка при создании эксперимента:", err);
      setError("Ошибка при создании эксперимента");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded shadow-md w-full max-w-md"
      >
        <h1 className="text-2xl font-semibold mb-6 text-center">
          Новый эксперимент
        </h1>

        {error && <div className="mb-4 text-red-600">{error}</div>}

        <label htmlFor="dataset" className="block mb-2 font-medium">
          Датасет
        </label>
        <select
          id="dataset"
          value={form.dataset_id}
          onChange={(e) => setForm({ ...form, dataset_id: Number(e.target.value) })}
          className="w-full px-3 py-2 border rounded mb-4"
          required
        >
          <option value="">Выберите датасет</option>
          {datasets.map((dataset) => (
            <option key={dataset.dataset_id} value={dataset.dataset_id}>
              {dataset.name}
            </option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Эпохи"
          value={form.epochs_num}
          onChange={(e) => setForm({ ...form, epochs_num: Number(e.target.value) })}
          className="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <input
          type="number"
          placeholder="Batch Size"
          value={form.batch_size}
          onChange={(e) => setForm({ ...form, batch_size: Number(e.target.value) })}
          className="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <input
          type="text"
          placeholder="Функция потерь"
          value={form.loss_function}
          onChange={(e) => setForm({ ...form, loss_function: e.target.value })}
          className="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <input
          type="number"
          step="0.0001"
          placeholder="Learning Rate"
          value={form.learning_rate}
          onChange={(e) => setForm({ ...form, learning_rate: Number(e.target.value) })}
          className="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <input
          type="text"
          placeholder="Оптимизатор"
          value={form.optimizer}
          onChange={(e) => setForm({ ...form, optimizer: e.target.value })}
          className="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <input
          type="number"
          placeholder="Кол-во слоёв"
          value={form.layers_num}
          onChange={(e) => setForm({ ...form, layers_num: Number(e.target.value) })}
          className="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <input
          type="number"
          placeholder="Нейронов в слое"
          value={form.neurons_num}
          onChange={(e) => setForm({ ...form, neurons_num: Number(e.target.value) })}
          className="w-full px-3 py-2 border rounded mb-6"
          required
        />

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
        >
          Создать
        </button>
      </form>
    </div>
  );
}