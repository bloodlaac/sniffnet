'use client';

import Link from "next/link";
import { useEffect, useState } from "react";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Toast from "../components/ui/Toast";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "../components/ui/Table";
import { getDatasets, getExperiments } from "@/lib/api";
import { getUser } from "@/lib/session";

const formatDate = (value) => {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("ru-RU");
  } catch (err) {
    return value;
  }
};

const statusBadge = (endTime) =>
  endTime
    ? { label: "Завершён", variant: "success" }
    : { label: "В процессе", variant: "warning" };

export default function ExperimentsPage() {
  const [user, setUser] = useState(null);
  const [experiments, setExperiments] = useState([]);
  const [datasets, setDatasets] = useState({});
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ message: "", variant: "info" });

  useEffect(() => {
    setUser(getUser());
  }, []);

  useEffect(() => {
    if (!user) return;
    const fetchData = async () => {
      setLoading(true);
      try {
        const [experimentsData, datasetsData] = await Promise.all([
          getExperiments(),
          getDatasets(),
        ]);

        const userExperiments = experimentsData.filter(
          (exp) => exp.user_id === user.user_id
        );
        const dsMap = datasetsData.reduce((acc, d) => {
          acc[d.dataset_id] = d.name;
          return acc;
        }, {});

        setDatasets(dsMap);
        setExperiments(userExperiments);
      } catch (err) {
        setToast({
          message: err.message || "Не удалось загрузить эксперименты",
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Эксперименты
          </h1>
          <p className="text-sm text-slate-600">
            Выберите эксперимент, чтобы открыть его детали.
          </p>
        </div>
        <Link href="/experiments/new">
          <Button>Новый эксперимент</Button>
        </Link>
      </div>

      {toast.message && (
        <Toast
          message={toast.message}
          variant={toast.variant}
          onClose={() => setToast({ message: "", variant: "info" })}
        />
      )}

      <Card className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-10 text-slate-600">
            Загружаем эксперименты...
          </div>
        ) : experiments.length === 0 ? (
          <div className="flex flex-col items-start gap-4 rounded-2xl bg-slate-50 px-5 py-6 text-left">
            <p className="text-base font-semibold text-slate-900">
              Вы пока не провели ни одного эксперимента
            </p>
          </div>
        ) : (
          <Table>
            <TableHead>
              <tr>
                <TableHeaderCell>ID</TableHeaderCell>
                <TableHeaderCell>Датасет</TableHeaderCell>
                <TableHeaderCell>Старт</TableHeaderCell>
                <TableHeaderCell>Завершение</TableHeaderCell>
                <TableHeaderCell>Статус</TableHeaderCell>
                <TableHeaderCell />
              </tr>
            </TableHead>
            <TableBody>
              {experiments.map((exp) => {
                const badge = statusBadge(exp.end_time);
                return (
                  <TableRow key={exp.experiment_id}>
                    <TableCell className="font-semibold text-slate-900">
                      #{exp.experiment_id}
                    </TableCell>
                    <TableCell>
                      {datasets[exp.dataset_id] || `Датасет ${exp.dataset_id}`}
                    </TableCell>
                    <TableCell className="text-slate-600">
                      {formatDate(exp.start_time)}
                    </TableCell>
                    <TableCell className="text-slate-600">
                      {formatDate(exp.end_time)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={badge.variant}>{badge.label}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href={`/experiments/${exp.experiment_id}`}>
                        <Button size="sm" variant="secondary">
                          Открыть
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
