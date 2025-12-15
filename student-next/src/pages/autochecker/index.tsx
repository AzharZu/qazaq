import { FormEvent, useMemo, useState } from "react";
import { AutoCheckerHtmlResponse, AutoCheckerMistake, autocheckerApi } from "@/lib/api/autochecker";

const emptyResult: AutoCheckerHtmlResponse = {
  ai_used: false,
  model: null,
  overall_score: 0,
  categories: { grammar: 0, vocabulary: 0, word_order: 0, clarity: 0 },
  mistakes: [],
  mentor_feedback: "",
  improved_version: "",
  recommendations: [],
};

const escapeHtml = (value: string) =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const highlightText = (source: string, mistakes: AutoCheckerMistake[]) => {
  if (!source) return "";
  let html = escapeHtml(source);
  const seen = new Set<string>();
  mistakes.forEach((m) => {
    const fragment = (m.fragment || "").trim();
    if (!fragment || seen.has(fragment)) return;
    const safe = escapeHtml(fragment);
    const pattern = new RegExp(escapeRegex(safe), "g");
    html = html.replace(pattern, `<mark>${safe}</mark>`);
    seen.add(fragment);
  });
  return html;
};

const clampScore = (value: number) => Math.max(0, Math.min(100, value));

export default function AutoCheckerPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AutoCheckerHtmlResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await autocheckerApi.check(text);
      if (!res.ai_used) {
        setError("ИИ недоступен. Проверка не выполнена.");
        setResult(null);
        return;
      }
      setResult(res);
    } catch (_err: any) {
      setError("ИИ недоступен. Проверка не выполнена.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const data = useMemo(() => result ?? emptyResult, [result]);
  const highlighted = highlightText(text, data.mistakes) || "<p class='text-slate'>Подсветка появится здесь.</p>";
  const improved = data.improved_version || "Корректированный текст появится здесь.";

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <header className="text-center space-y-3">
        <p className="text-xs uppercase tracking-[0.4em] text-gold">AutoChecker</p>
        <h1 className="text-hero font-semibold text-white">ИИ-помощник для вашего текста</h1>
        <p className="text-sm text-slate">
          Проверка грамматики, лексики и пунктуации на казахском языке с мгновенной подсветкой ошибок и
          рекомендациями.
        </p>
      </header>

      <form onSubmit={submit} className="card-surface space-y-4 p-6">
        <label className="flex flex-col gap-3">
          <span className="text-sm font-semibold text-ink/80">Введите текст для проверки</span>
          <div className="relative">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              className="w-full rounded-xl border border-slate/40 bg-midnight px-4 py-4 text-base text-ink shadow-soft placeholder:text-slate/60 focus:border-gold focus:outline-none"
              placeholder="Жазыңыз немесе вставьте текст на казахском..."
            />
            <button
              type="button"
              aria-label="Голосовой ввод"
              className="absolute right-3 top-3 rounded-full border border-slate/50 bg-panel px-3 py-2 text-xs font-semibold uppercase tracking-wide text-ink/80 transition hover:border-gold hover:text-white"
            >
              🎤
            </button>
          </div>
        </label>
        <div className="flex items-center justify-between text-sm text-ink/70">
          <span>Символов: {text.length}</span>
          {result && (
            <span className="rounded-full bg-slate/40 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-gold">
              🤖 Проверено ИИ ({data.model || "Gemini"})
            </span>
          )}
        </div>
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="w-full rounded-xl bg-gold px-6 py-3 text-center text-sm font-semibold uppercase tracking-wide text-night transition hover:bg-goldDark disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Проверяем..." : "Проверить через ИИ"}
        </button>
      </form>

      {error && (
        <div className="rounded-xl border border-red-500/50 bg-red-900/30 px-6 py-4 text-sm text-red-200">
          ⚠️ {error}
        </div>
      )}

      {result && !error && (
        <div className="space-y-6">
          <section className="card-surface p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Оценка текста</h3>
              <span className="text-xs uppercase tracking-wide text-slate">0-100</span>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Progress label="Grammar" value={clampScore(data.categories.grammar)} />
              <Progress label="Vocabulary" value={clampScore(data.categories.vocabulary)} />
              <Progress label="Word Order" value={clampScore(data.categories.word_order)} />
              <Progress label="Clarity" value={clampScore(data.categories.clarity)} />
            </div>
            <div className="flex items-center justify-between rounded-lg border border-slate/40 bg-midnight/60 px-4 py-3">
              <span className="text-sm text-ink/80">Общий балл</span>
              <span className="text-2xl font-semibold text-gold">{clampScore(data.overall_score)}</span>
            </div>
          </section>

          <section className="card-surface p-6 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold uppercase tracking-wide text-gold">Qazaq Mentor говорит</p>
              <span className="rounded-full border border-slate/40 px-3 py-1 text-xs text-ink/70">
                🤖 {data.model || "Gemini"}
              </span>
            </div>
            <p className="text-base text-ink/90">
              {data.mentor_feedback || "Комментарий появится после проверки."}
            </p>
          </section>

          <section className="card-surface p-6 space-y-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-gold">Ваш текст с подсветкой ошибок</p>
              <h3 className="text-xl font-semibold text-white">Before</h3>
              <div
                className="mt-2 max-w-none rounded-lg border border-slate/40 bg-midnight/60 p-4 text-base leading-relaxed text-ink"
                dangerouslySetInnerHTML={{ __html: highlighted }}
              />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white">After</h3>
              <div className="mt-2 rounded-lg border border-slate/40 bg-midnight/60 p-4 text-sm text-ink whitespace-pre-line">
                {improved}
              </div>
            </div>
          </section>

          <section className="card-surface p-6 space-y-4">
            <p className="text-sm font-semibold uppercase tracking-wide text-gold">Найденные ошибки</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {data.mistakes.length === 0 && (
                <div className="rounded-lg border border-slate/40 bg-midnight/60 p-4 text-sm text-ink/70">
                  Ошибок не обнаружено.
                </div>
              )}
              {data.mistakes.map((err, idx) => (
                <article
                  key={`${err.fragment}-${idx}`}
                  className="rounded-lg border border-slate/40 bg-midnight/60 p-4 shadow-soft space-y-2"
                >
                  <span className="text-xs uppercase tracking-wide text-gold">Фрагмент</span>
                  <p className="text-sm text-ink">{err.fragment || "—"}</p>
                  <p className="text-sm text-ink/90">Проблема: {err.issue || "—"}</p>
                  <p className="text-sm text-ink/80">Почему: {err.explanation || "—"}</p>
                  <p className="text-sm text-gold">Вариант: {err.suggestion || "—"}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="card-surface p-6 space-y-3">
            <p className="text-sm font-semibold uppercase tracking-wide text-gold">Рекомендации</p>
            <ul className="space-y-2 text-sm text-ink">
              {data.recommendations.length === 0 && <li className="text-slate">Нет рекомендаций.</li>}
              {data.recommendations.map((item, idx) => (
                <li key={idx} className="flex gap-2">
                  <span className="mt-1 h-2 w-2 rounded-full bg-gold" aria-hidden />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="card-surface p-6 space-y-3">
            <p className="text-sm font-semibold uppercase tracking-wide text-gold">Предложенный вариант текста</p>
            <div className="rounded-lg border border-slate/40 bg-midnight/60 p-4 text-sm text-ink whitespace-pre-line">
              {improved}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

type ProgressProps = { label: string; value: number };

function Progress({ label, value }: ProgressProps) {
  const width = Math.min(100, Math.max(0, value));
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm text-ink/80">
        <span>{label}</span>
        <span className="text-gold font-semibold">{value.toFixed(0)}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-slate/50">
        <div className="h-2 rounded-full bg-gold" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}
