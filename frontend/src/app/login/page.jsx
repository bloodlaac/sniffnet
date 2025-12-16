"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Toast from "../components/ui/Toast";
import { login } from "@/lib/api";
import { setUser } from "@/lib/session";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [toast, setToast] = useState({ message: "", variant: "info" });
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setToast({ message: "Заполните логин и пароль", variant: "warning" });
      return;
    }

    setLoading(true);
    setToast({ message: "", variant: "info" });
    try {
      const user = await login(username, password);
      setUser(user);
      router.replace("/experiments");
    } catch (err) {
      setToast({
        message: err.message || "Неверные данные для входа",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-120px)] items-center justify-center">
      <Card className="w-full max-w-md p-8">
        <div className="mb-6 space-y-2 text-center">
          <p className="text-sm uppercase tracking-wide text-blue-600">Вход</p>
          <h1 className="text-2xl font-bold text-slate-900">
            Авторизация
          </h1>
        </div>

        {toast.message && (
          <div className="mb-4">
            <Toast
              message={toast.message}
              variant={toast.variant}
              onClose={() => setToast({ message: "", variant: "info" })}
            />
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Логин"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
          <Input
            label="Пароль"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Входим..." : "Войти"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
