"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Badge from "./components/ui/Badge";
import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import { getUser } from "@/lib/session";

const features = [
  {
    title: "Проверка продуктов",
    description: "Загружайте изображение продукта и получайте оценку его свежести.",
  },
  {
    title: "Эксперименты",
    description:
      "Подбирайте параметры обучения нейросети и определяйте качество продуктов, используя новые модели.",
  },
];

export default function Home() {
  const [username, setUsername] = useState("");

  useEffect(() => {
    const u = getUser();
    setUsername(u?.username || "");
  }, []);

  return (
    <div className="space-y-10">
      <Card className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_20%_20%,rgba(37,99,235,0.12),transparent_35%),radial-gradient(circle_at_80%_0%,rgba(14,165,233,0.15),transparent_30%)]" />
        <div className="relative grid gap-10 p-8 md:grid-cols-2 md:p-12">
          <div className="space-y-5">
            <h1 className="text-4xl font-black leading-tight text-slate-900 md:text-5xl">
              SniffNet - Ваш эксперт по продуктам
            </h1>
            <p className="text-lg text-slate-600">
              Проверяйте содержимое вашей корзины на испорченность в пару кликов.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link href="/experiments/new">
                <Button size="lg">Новый эксперимент</Button>
              </Link>
              <Link href="/predict">
                <Button variant="secondary" size="lg">
                  Проверить фото
                </Button>
              </Link>
            </div>
          </div>
          <div className="glass-panel relative rounded-2xl p-6 shadow-lg">
            <div className="mb-4 flex items-center gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-700">
                  Инструменты мониторинга
                </p>
              </div>
            </div>
            <div className="space-y-3 text-sm text-slate-700">
              <div className="flex items-center justify-between rounded-xl border border-blue-50 bg-blue-50/70 px-4 py-3">
                <div>
                  <p className="text-base font-semibold text-slate-900">
                    Последний эксперимент
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-100 bg-white px-4 py-3">
                  <p className="text-xs text-slate-500">Датасет</p>
                  <p className="text-base font-semibold text-slate-900">
                    Fruits-2024
                  </p>
                  <p className="text-xs text-slate-500">12 классов</p>
                </div>
                <div className="rounded-xl border border-slate-100 bg-white px-4 py-3">
                  <p className="text-xs text-slate-500">Метрики</p>
                  <p className="text-base font-semibold text-slate-900">
                    Acc 92%
                  </p>
                  <p className="text-xs text-emerald-600">+4% к прошлому</p>
                </div>
              </div>
              <div className="rounded-xl border border-slate-100 bg-white px-4 py-3">
                <p className="text-xs text-slate-500">Конфигурация</p>
                <p className="text-sm font-semibold text-slate-900">
                  epochs: 15 · batch: 32 · lr: 0.001
                </p>
                <p className="text-xs text-slate-500">optimizer: Adam</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">
              Возможности
            </h2>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {features.map((feature) => (
            <Card key={feature.title} className="p-6">
              <h3 className="text-lg font-semibold text-slate-900">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{feature.description}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
