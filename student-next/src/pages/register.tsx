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
    <div className="mx-auto max-w-xl space-y-6 rounded-2xl border border-slate/40 bg-panel p-8 shadow-card">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-gold">Создать аккаунт</p>
        <h1 className="text-3xl font-semibold text-white">Регистрация</h1>
        <p className="text-sm text-ink/80">Доступ ко всем курсам, тестам, словарю и проверке текста.</p>
      </div>
      <form onSubmit={submit} className="space-y-4">
        <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
          Имя
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
            placeholder="Ваше имя"
          />
        </label>
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
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-gold px-6 py-3 text-base font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Создаем аккаунт..." : "Зарегистрироваться"}
        </button>
      </form>
      <div className="flex items-center justify-between text-sm text-ink/80">
        <span>Уже с нами?</span>
        <Link href="/login" className="font-semibold text-gold hover:text-white">
          Войти
        </Link>
      </div>
    </div>
  );
}
