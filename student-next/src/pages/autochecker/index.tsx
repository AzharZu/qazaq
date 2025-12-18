import Head from "next/head";
import { useMemo, useState } from "react";
import DOMPurify from "isomorphic-dompurify";
import { autocheckerApi, TextCheckIssue, TextCheckResponse } from "@/lib/api/autochecker";

const LANG_OPTIONS: Array<{ value: "ru" | "kk"; label: string }> = [
  { value: "ru", label: "Русский" },
  { value: "kk", label: "Қазақша" },
];

const COPY = {
  ru: {
    title: "ИИ-помощник для вашего текста",
    subtitle: "Проверка грамматики, лексики и орфографии с подсветкой ошибок и рекомендациями.",
    inputLabel: "Текст для проверки",
    placeholder: "Введите текст для проверки...",
    languageLabel: "Язык проверки",
    checkButton: "Проверить через ИИ",
    summaryTitle: "Qazaq Mentor говорит:",
    highlightTitle: "Ваш текст с подсветкой ошибок",
    before: "До",
    after: "После",
    issuesTitle: "Найденные ошибки",
    recommendations: "Рекомендации",
    suggested: "Предложенный вариант текста",
    noIssues: "Ошибки не найдены",
    noRecommendations: "Рекомендаций пока нет",
    suggestedHint: "Это предложение не должно восприниматься как готовый текст «под ключ».",
    scoreLabel: "Оценка",
  },
  kk: {
    title: "Мәтінге арналған AI-көмекші",
    subtitle: "Грамматика, лексика және орфография бойынша тексеру, қателерді белгілеу және ұсыныстар.",
    inputLabel: "Тексерілетін мәтін",
    placeholder: "Мәтінді енгізіңіз...",
    languageLabel: "Тексеру тілі",
    checkButton: "ИИ арқылы тексеру",
    summaryTitle: "Qazaq Mentor айтады:",
    highlightTitle: "Қателері белгіленген мәтін",
    before: "Алдыңғы нұсқа",
    after: "Кейінгі нұсқа",
    issuesTitle: "Табылған қателер",
    recommendations: "Ұсыныстар",
    suggested: "Ұсынылған мәтін",
    noIssues: "Қателер табылмады",
    noRecommendations: "Ұсыныстар жоқ",
    suggestedHint: "Бұл нұсқа дайын мәтін емес, тек ИИ-дің ұсынысы.",
    scoreLabel: "Баға",
  },
};

const ALLOWED_TAGS = ["mark", "span", "br", "p"];
const ALLOWED_ATTR = ["data-error-id", "class"];

function ScoreBar({ label, value, max = 10 }: { label: string; value: number; max?: number }) {
  const safe = Math.max(0, Math.min(max, Math.round(value)));
  const percent = Math.round((safe / max) * 100);
  return (
    <div className="space-y-2 rounded-xl bg-midnight p-4 shadow-inner">
      <div className="flex items-center justify-between text-sm font-semibold text-ink/80">
        <span>{label}</span>
        <span className="text-ink">{safe}/{max}</span>
      </div>
      <div className="h-3 w-full rounded-full bg-slate/50 shadow-inner">
        <div className="h-3 rounded-full bg-gradient-to-r from-gold to-goldDark transition-all" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function IssueCard({ issue, lang }: { issue: TextCheckIssue; lang: "ru" | "kk" }) {
  const typeLabels =
    lang === "kk"
      ? { grammar: "Грамматика", lexicon: "Лексика", spelling: "Орфография", punctuation: "Тыныс белгілері" }
      : { grammar: "Грамматика", lexicon: "Лексика", spelling: "Орфография", punctuation: "Пунктуация" };
  const label = typeLabels[issue.type as keyof typeof typeLabels] || issue.type;

  return (
    <div className="space-y-3 rounded-xl bg-midnight p-4 shadow-inner">
      <div className="flex items-center justify-between gap-3">
        <span className="rounded-full bg-slate px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/80">{label}</span>
        <span className="rounded-full bg-slate/60 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-ink/70">
          {issue.severity}
        </span>
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-white">{issue.title}</p>
        <p className="text-sm text-ink/80">{issue.explanation}</p>
      </div>
      <div className="space-y-1 rounded-lg bg-slate/50 p-3 text-sm text-ink/90">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink/70">{lang === "kk" ? "Дейін" : "До"}</p>
        <p>{issue.before || "—"}</p>
      </div>
      <div className="space-y-1 rounded-lg bg-slate/50 p-3 text-sm text-ink/90">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink/70">{lang === "kk" ? "Кейін" : "После"}</p>
        <p>{issue.after || "—"}</p>
      </div>
    </div>
  );
}

export default function AutoCheckerPage() {
  const [language, setLanguage] = useState<"ru" | "kk">("kk");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TextCheckResponse | null>(null);

  const copy = COPY[language];

  const sanitizedHighlight = useMemo(() => {
    const source = (result?.highlighted_html && result.highlighted_html.trim()) || result?.before_text || "";
    if (!source) return "";
    return DOMPurify.sanitize(source, { ALLOWED_TAGS, ALLOWED_ATTR });
  }, [result]);

  const mentorNote = useMemo(() => {
    if (result?.recommendations?.length) return result.recommendations[0];
    if (result?.issues?.length) return result.issues[0].explanation;
    return language === "kk" ? "Мәтінді тексеру үшін жоғарыда мәтін енгізіңіз." : "Введите текст выше, чтобы получить проверку.";
  }, [language, result]);

  const handleCheck = async () => {
    if (!text.trim()) {
      setError(language === "kk" ? "Мәтін бос." : "Текст пустой.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await autocheckerApi.textCheck({ text, language, mode: "full" });
      if (!res.ok) {
        setResult(null);
        setError(res.error || (language === "kk" ? "LLM қатесі" : "Ошибка LLM"));
      } else {
        setResult(res);
      }
    } catch (err: any) {
      const data = err?.response?.data;
      const status = err?.response?.status;
      let message = data?.error || data?.detail || err?.message || "Request failed";
      if (status === 401) message = language === "kk" ? "Кіру қажет (401)." : "Нужна авторизация (401).";
      if (status && status >= 500) message = language === "kk" ? "Сервис уақытша қолжетімсіз." : "Сервис временно недоступен.";
      setResult(null);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>AutoChecker</title>
      </Head>
      <div className="space-y-8">
        <section className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-wide text-gold">AutoChecker</p>
              <h1 className="text-3xl font-semibold text-white">{copy.title}</h1>
              <p className="text-sm text-ink/80">{copy.subtitle}</p>
            </div>
            {result?.request_id ? (
              <span className="rounded-full bg-slate px-3 py-1 text-xs font-mono text-ink/80">req: {result.request_id}</span>
            ) : null}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-ink/80" htmlFor="autochecker-text">
              {copy.inputLabel}
            </label>
            <textarea
              id="autochecker-text"
              className="w-full rounded-xl border border-slate/50 bg-midnight px-4 py-3 text-base text-ink shadow-inner placeholder:text-ink/50 focus:border-gold focus:outline-none"
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={copy.placeholder}
            />
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-ink/60">
              <span>{text.length} символов</span>
              <div className="flex items-center gap-2">
                <span>{copy.languageLabel}</span>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as "ru" | "kk")}
                  className="rounded-lg border border-slate/50 bg-midnight px-3 py-1 text-xs text-ink shadow-inner focus:border-gold focus:outline-none"
                >
                  {LANG_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleCheck}
              disabled={loading}
              className="rounded-xl bg-gold px-6 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? (language === "kk" ? "Тексеріп жатырмыз..." : "Проверяем...") : copy.checkButton}
            </button>
            <button
              type="button"
              onClick={() => {
                setText("");
                setResult(null);
                setError(null);
              }}
              className="rounded-xl bg-slate px-6 py-3 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
            >
              {language === "kk" ? "Тазарту" : "Очистить"}
            </button>
          </div>

          {error ? <div className="rounded-xl border border-red-500/40 bg-red-900/40 px-4 py-3 text-sm text-red-100">{error}</div> : null}
        </section>

        {result ? (
          <section className="space-y-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl bg-panel p-5 shadow-card">
                <p className="text-sm font-semibold uppercase tracking-wide text-gold">{language === "kk" ? "Деңгей" : "Уровень"}</p>
                <div className="mt-3 flex items-center gap-3">
                  <span className="rounded-full bg-slate px-3 py-1 text-sm font-semibold text-ink">{result.level}</span>
                  <span className="rounded-full bg-slate/60 px-3 py-1 text-xs font-semibold text-ink/80">{copy.scoreLabel}: {result.scores.overall}</span>
                </div>
                <p className="mt-2 text-xs text-ink/60">{copy.languageLabel}: {language === "kk" ? "Қазақша" : "Русский"}</p>
              </div>
              <div className="rounded-2xl bg-panel p-5 shadow-card md:col-span-2">
                <div className="grid gap-3 md:grid-cols-2">
                  <ScoreBar label={language === "kk" ? "Грамматика" : "Грамматика"} value={result.scores.grammar} />
                  <ScoreBar label={language === "kk" ? "Лексика" : "Лексика"} value={result.scores.lexicon} />
                  <ScoreBar label={language === "kk" ? "Орфография" : "Орфография"} value={result.scores.spelling} />
                  <ScoreBar label={language === "kk" ? "Тыныс белгілері" : "Пунктуация"} value={result.scores.punctuation} />
                </div>
              </div>
            </div>

            <div className="rounded-2xl bg-panel p-5 shadow-card">
              <p className="text-sm font-semibold text-gold">{copy.summaryTitle}</p>
              <p className="mt-2 text-sm text-ink">{mentorNote}</p>
            </div>

            <div className="rounded-2xl bg-panel p-5 shadow-card">
              <p className="text-sm font-semibold text-gold">{copy.highlightTitle}</p>
              <div
                className="mt-3 min-h-[120px] rounded-xl bg-midnight p-4 text-sm leading-relaxed text-ink shadow-inner"
                dangerouslySetInnerHTML={{ __html: sanitizedHighlight || result.before_text }}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl bg-panel p-5 shadow-card">
                <p className="text-sm font-semibold text-gold">{copy.before}</p>
                <p className="mt-2 min-h-[120px] rounded-xl bg-midnight p-4 text-sm text-ink shadow-inner whitespace-pre-wrap">{result.before_text || "—"}</p>
              </div>
              <div className="rounded-2xl bg-panel p-5 shadow-card">
                <p className="text-sm font-semibold text-gold">{copy.after}</p>
                <p className="mt-2 min-h-[120px] rounded-xl bg-midnight p-4 text-sm text-ink shadow-inner whitespace-pre-wrap">{result.after_text || "—"}</p>
              </div>
            </div>

            <div className="rounded-2xl bg-panel p-5 shadow-card">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-gold">{copy.issuesTitle}</p>
                <span className="text-xs text-ink/60">{result.issues?.length || 0}</span>
              </div>
              {result.issues?.length ? (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  {result.issues.map((issue) => (
                    <IssueCard key={issue.id} issue={issue} lang={language} />
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-ink/70">{copy.noIssues}</p>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl bg-panel p-5 shadow-card">
                <p className="text-sm font-semibold text-gold">{copy.recommendations}</p>
                {result.recommendations?.length ? (
                  <ul className="mt-3 space-y-2 text-sm text-ink">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex gap-2">
                        <span className="mt-1 h-2 w-2 rounded-full bg-gold" aria-hidden />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-ink/70">{copy.noRecommendations}</p>
                )}
              </div>

              <div className="rounded-2xl bg-panel p-5 shadow-card">
                <p className="text-sm font-semibold text-gold">{copy.suggested}</p>
                <p className="mt-2 min-h-[120px] rounded-xl bg-midnight p-4 text-sm text-ink shadow-inner whitespace-pre-wrap">{result.suggested_text || "—"}</p>
                <p className="mt-2 text-xs text-ink/50">{copy.suggestedHint}</p>
              </div>
            </div>
          </section>
        ) : null}
      </div>
    </>
  );
}
