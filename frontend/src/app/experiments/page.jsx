'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/apiFetch';

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    async function fetchExperiments() {
      try {
        const data = await apiFetch('/experiments');
        setExperiments(data);
      } catch (error) {
        console.error('Ошибка при загрузке экспериментов:', error.message);
      }
    }

    fetchExperiments();
  }, []);

  const openExperimentDetails = async (id) => {
    try {
      const config = await apiFetch(`/experiments/${id}`);
      setSelectedExperiment(config);
      setModalOpen(true);
    } catch (error) {
      console.error('Ошибка при загрузке деталей эксперимента:', error.message);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto text-center">
      <h1 style={{fontSize: '30px', marginBottom: '30px'}}>Список экспериментов</h1>
      
      <table className="w-full border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-2 border">ID</th>
            <th className="p-2 border">Дата начала</th>
            <th className="p-2 border">Дата окончания</th>
            <th className="p-2 border">Действия</th>
          </tr>
        </thead>
        <tbody>
          {experiments.map((exp) => (
            <tr key={exp.experiment_id} className="hover:bg-blue-50">
              <td className="p-2 border">{exp.experiment_id}</td>
              <td className="p-2 border">
                {new Date(exp.start_time).toLocaleString("ru-RU", { timeZone: "Europe/Samara" })}
              </td>
              <td className="p-2 border">
                {exp.end_time ? new Date(exp.end_time).toLocaleString("ru-RU", { timeZone: "Europe/Samara" }) : '—'}
              </td>
              <td className="p-2 border">
                <button
                  onClick={() => openExperimentDetails(exp.experiment_id)}
                  className="text-blue-600 hover:underline"
                >
                  Подробнее
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Link href="/experiments/new">
        <button style = {{ border: '3px solid blue', borderRadius: 25, marginTop: 80, position: 'absolute', left: '50%', transform: 'translate(-50%, -50%)' }} className="bg-blue-500 text-white px-4 py-3 rounded hover:bg-blue-700 transition">
          Новый эксперимент
        </button>
      </Link>

      {modalOpen && selectedExperiment && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg relative">
            <h2 className="text-xl font-semibold mb-4">Конфигурация эксперимента #{selectedExperiment.experiment_id}</h2>
            <ul className="space-y-2 text-sm">
              <li><strong>Batch Size:</strong> {selectedExperiment.batch_size}</li>
              <li><strong>Epochs:</strong> {selectedExperiment.epochs_num}</li>
              <li><strong>Loss Function:</strong> {selectedExperiment.loss_function}</li>
              <li><strong>Learning Rate:</strong> {selectedExperiment.learning_rate}</li>
              <li><strong>Optimizer:</strong> {selectedExperiment.optimizer}</li>
              <li><strong>Layers:</strong> {selectedExperiment.layers_num}</li>
              <li><strong>Neurons:</strong> {selectedExperiment.neurons_num}</li>
            </ul>
            <p><strong>Train Accuracy:</strong> {selectedExperiment.train_accuracy ?? "ещё не рассчитано"}</p>
            <p><strong>Train Loss:</strong> {selectedExperiment.train_loss ?? "ещё не рассчитано"}</p>


            <button
              className="absolute top-2 right-3 text-gray-600 hover:text-black"
              onClick={() => setModalOpen(false)}
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}