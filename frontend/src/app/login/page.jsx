"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../lib/apiFetch";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const result = await apiFetch("/auth/login", {
        method: "POST",
        body: { username, password },
      });
      localStorage.setItem("user_id", result.user_id);
      router.push("/experiments");
    } catch (err) {
      setError("Неверные данные для входа");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded shadow-md w-full max-w-sm"
      >
        <h1 className="text-2xl font-semibold mb-6 text-center">
          Вход в систему
        </h1>

        {error && (
          <div className="mb-4 text-red-600 text-sm">
            Ошибка: {error}
          </div>
        )}

        <label htmlFor="username" className="block mb-2 font-medium">
          Логин
        </label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Введите логин"
          className="w-full px-3 py-2 border rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />

        <label htmlFor="password" className="block mb-2 font-medium">
          Пароль
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Введите пароль"
          className="w-full px-3 py-2 border rounded mb-6 focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />

        <button
          type="submit"
          className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          Войти
        </button>
      </form>
    </div>
  );
}