import Link from "next/link";
import { useRouter } from "next/router";
import { FormEvent, useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";

export default function LoginPage() {
  const router = useRouter();
  const { token, login, error, loading } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      router.replace("/courses");
    }
  }, [token, router]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await login(email, password);
      router.push("/courses");
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || error || "Не удалось войти");
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-6 rounded-2xl border border-slate/40 bg-panel p-8 shadow-card">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-gold">Добро пожаловать</p>
        <h1 className="text-3xl font-semibold text-white">Вход</h1>
        <p className="text-sm text-ink/80">Используйте email и пароль, чтобы перейти к курсам и урокам.</p>
      </div>
      <form onSubmit={submit} className="space-y-4">
        <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
            placeholder="you@example.com"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
          Пароль
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
            placeholder="••••••••"
          />
        </label>
        {(formError || error) && <p className="text-sm text-red-400">{formError || error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-gold px-6 py-3 text-base font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Входим..." : "Войти"}
        </button>
      </form>
      <div className="flex items-center justify-between text-sm text-ink/80">
        <span>Нет аккаунта?</span>
        <Link href="/register" className="font-semibold text-gold hover:text-white">
          Зарегистрироваться
        </Link>
      </div>
    </div>
  );
}
