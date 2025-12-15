import Link from "next/link";
import { useRouter } from "next/router";
import { FormEvent, useState } from "react";
import { useAuthStore } from "@/store/authStore";

export default function RegisterPage() {
  const router = useRouter();
  const { register, loading } = useAuthStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await register({ email, password, name });
      router.push("/courses");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Не удалось зарегистрироваться");
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-6 rounded-2xl bg-white p-8 shadow-sm">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">Создать аккаунт</p>
        <h1 className="text-3xl font-semibold text-gray-900">Регистрация</h1>
        <p className="text-sm text-gray-700">Доступ ко всем курсам, тестам, словарю и проверке текста.</p>
      </div>
      <form onSubmit={submit} className="space-y-4">
        <label className="flex flex-col gap-2 text-sm font-semibold text-gray-800">
          Имя
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-3 text-base text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none"
            placeholder="Ваше имя"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-semibold text-gray-800">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-3 text-base text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none"
            placeholder="you@example.com"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-semibold text-gray-800">
          Пароль
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-3 text-base text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none"
            placeholder="••••••••"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-blue-600 px-6 py-3 text-base font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
        >
          {loading ? "Создаем аккаунт..." : "Зарегистрироваться"}
        </button>
      </form>
      <div className="flex items-center justify-between text-sm text-gray-700">
        <span>Уже с нами?</span>
        <Link href="/login" className="font-semibold text-blue-700 hover:text-blue-800">
          Войти
        </Link>
      </div>
    </div>
  );
}
