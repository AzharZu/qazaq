import { FormEvent, useMemo, useState } from "react";
import { autocheckerApi, FreeWritingResult, TextCheckResponse } from "../api/autochecker";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardTitle } from "../components/ui/card";
import { Textarea } from "../components/ui/textarea";
import { useToast } from "../components/ui/use-toast";

const LANG_OPTIONS = [
  { value: "kk", label: "Kazakh (kk)" },
  { value: "ru", label: "Russian (ru)" },
  { value: "en", label: "English (en)" },
];

export default function AutocheckerPage() {
  const [health, setHealth] = useState<{ ok: boolean; provider: string; key_present: boolean; error?: string; request_id?: string } | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [form, setForm] = useState({ prompt: "", student_answer: "", rubric: "", language: "kk" });
  const [result, setResult] = useState<FreeWritingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [textCheckInput, setTextCheckInput] = useState({ text: "", language: "kk" as "kk" | "ru" });
  const [textResult, setTextResult] = useState<TextCheckResponse | null>(null);
  const [textLoading, setTextLoading] = useState(false);
  const [textError, setTextError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const runHealth = async () => {
    setHealthLoading(true);
    try {
      const res = await autocheckerApi.health();
      setHealth(res);
      if (!res.ok) {
        toast({ title: "LLM недоступен", description: res.error || "Проверьте ключ", variant: "destructive" });
      }
    } catch (err: any) {
      const data = err?.response?.data;
      const message = data?.error || data?.detail || err?.message || "Health check failed";
      setHealth({ ok: false, provider: "llm", key_present: false, error: message });
      toast({ title: "Health check failed", description: message, variant: "destructive" });
    } finally {
      setHealthLoading(false);
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await autocheckerApi.checkFreeWriting({
        prompt: form.prompt,
        student_answer: form.student_answer,
        rubric: form.rubric || undefined,
        language: form.language || "kk",
      });
      if (!res.ok) {
        setResult(null);
        setError(res.error || "Gemini вернул ошибку");
      } else {
        setResult(res);
      }
    } catch (err: any) {
      const status = err?.response?.status;
      const data = err?.response?.data;
      let message = data?.error || data?.detail || err?.message || "Не удалось выполнить проверку";
      if (status === 401) message = "401 Unauthorized — выполните вход в админку.";
      else if (status && status >= 500) message = "Сервис недоступен (500). Проверьте ключ или сеть.";
      setResult(null);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const runTextCheck = async () => {
    if (!textCheckInput.text.trim()) {
      setTextError("Введите текст для проверки");
      return;
    }
    setTextLoading(true);
    setTextError(null);
    try {
      const res = await autocheckerApi.textCheck({
        text: textCheckInput.text,
        language: textCheckInput.language,
        mode: "full",
      });
      if (!res.ok) {
        setTextResult(null);
        setTextError(res.error || "LLM вернул ошибку");
      } else {
        setTextResult(res);
      }
    } catch (err: any) {
      const status = err?.response?.status;
      const data = err?.response?.data;
      let message = data?.error || data?.detail || err?.message || "Не удалось выполнить проверку";
      if (status === 401) message = "401 Unauthorized — выполните вход в админку.";
      else if (status && status >= 500) message = "Сервис недоступен (500). Проверьте ключ или сеть.";
      setTextResult(null);
      setTextError(message);
    } finally {
      setTextLoading(false);
    }
  };

  const statusLabel = useMemo(() => {
    if (!health) return "Неизвестно";
    if (!health.key_present) return "Ключ не найден";
    return health.ok ? "OK" : "Ошибка";
  }, [health]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Autochecker</p>
          <h1 className="text-2xl font-semibold text-slate-900">LLM integration (Grok-compatible)</h1>
          <p className="text-sm text-slate-600">Проверка ключа, быстрый health и ручные проверки.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={runHealth} disabled={healthLoading}>
            {healthLoading ? "Проверяем..." : "Test LLM"}
          </Button>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              health?.ok ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"
            }`}
          >
            {statusLabel}
          </span>
        </div>
      </div>

      <Card className="bg-white shadow-sm">
        <CardContent className="space-y-4 p-4">
          <div className="flex items-center justify-between">
            <CardTitle>Text check (LLM)</CardTitle>
            {textResult?.request_id ? <span className="text-[10px] font-mono text-slate-500">req: {textResult.request_id}</span> : null}
          </div>

          <div className="space-y-3">
            <label className="text-sm font-semibold text-slate-700">Текст</label>
            <Textarea
              rows={4}
              value={textCheckInput.text}
              onChange={(e) => setTextCheckInput((prev) => ({ ...prev, text: e.target.value }))}
              placeholder="Введите текст, который нужно проверить (ru/kk)"
            />
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Символов: {textCheckInput.text.length}</span>
              <div className="flex items-center gap-2">
                <span>Язык</span>
                <select
                  className="rounded-md border border-slate-200 bg-white px-3 py-1 text-xs"
                  value={textCheckInput.language}
                  onChange={(e) => setTextCheckInput((prev) => ({ ...prev, language: e.target.value as "kk" | "ru" }))}
                >
                  <option value="kk">Kazakh (kk)</option>
                  <option value="ru">Russian (ru)</option>
                </select>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button type="button" onClick={runTextCheck} disabled={textLoading || !textCheckInput.text.trim()}>
                {textLoading ? "Проверяем..." : "Проверить текст"}
              </Button>
              <Button
                variant="outline"
                type="button"
                onClick={() => {
                  setTextCheckInput({ text: "", language: "kk" });
                  setTextResult(null);
                  setTextError(null);
                }}
              >
                Сбросить
              </Button>
            </div>
          </div>

          {textError ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{textError}</div> : null}

          {textResult?.ok ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2 rounded-md border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Level</p>
                <p className="text-2xl font-bold text-slate-900">{textResult.level}</p>
                <p className="text-xs text-slate-500">Overall: {textResult.scores.overall}</p>
                <p className="text-xs text-slate-500">Language: {textResult.language}</p>
              </div>
              <div className="space-y-2 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">
                <p className="text-xs uppercase tracking-wide text-slate-500">Рекомендации</p>
                {textResult.recommendations?.length ? (
                  <ul className="list-disc space-y-1 pl-4">
                    {textResult.recommendations.map((r, idx) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-500">Нет рекомендаций</p>
                )}
              </div>
              <div className="md:col-span-2 space-y-2 rounded-md border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">После</p>
                <p className="whitespace-pre-wrap text-sm text-slate-800">{textResult.after_text || "—"}</p>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="bg-white shadow-sm">
        <CardContent className="space-y-4 p-4">
          <div className="flex items-center justify-between">
            <CardTitle>Free writing check</CardTitle>
            {result?.model ? <span className="text-xs text-slate-500">model: {result.model}</span> : null}
          </div>
          <form onSubmit={submit} className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Prompt / Task</label>
                <Textarea
                  rows={4}
                  value={form.prompt}
                  onChange={(e) => setForm((prev) => ({ ...prev, prompt: e.target.value }))}
                  placeholder="Опишите задание, которое решает студент"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Rubric (optional)</label>
                <Textarea
                  rows={4}
                  value={form.rubric}
                  onChange={(e) => setForm((prev) => ({ ...prev, rubric: e.target.value }))}
                  placeholder="Критерии оценивания"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Student answer</label>
              <Textarea
                rows={6}
                value={form.student_answer}
                onChange={(e) => setForm((prev) => ({ ...prev, student_answer: e.target.value }))}
                placeholder="Ответ студента"
              />
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Символов: {form.student_answer.length}</span>
                <div className="flex items-center gap-2">
                  <span>Язык</span>
                  <select
                    className="rounded-md border border-slate-200 bg-white px-3 py-1 text-xs"
                    value={form.language}
                    onChange={(e) => setForm((prev) => ({ ...prev, language: e.target.value }))}
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
            <div className="flex items-center gap-3">
              <Button type="submit" disabled={loading || !form.prompt || !form.student_answer}>
                {loading ? "Проверяем..." : "Check"}
              </Button>
              <Button variant="outline" type="button" onClick={() => setForm({ prompt: "", student_answer: "", rubric: "", language: "kk" })}>
                Сбросить
              </Button>
            </div>
          </form>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}

          {result?.ok ? (
            <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Score</p>
                  <p className="text-3xl font-bold text-slate-900">{result.score ?? "—"}</p>
                </div>
                <div className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-white">{result.level || "—"}</div>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800">Feedback</p>
                <p className="text-sm text-slate-700">{result.feedback || "—"}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800">Corrections</p>
                {result.corrections && result.corrections.length ? (
                  <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                    {result.corrections.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-600">Нет исправлений.</p>
                )}
              </div>
              {result.request_id ? <p className="text-[10px] font-mono text-slate-500">req: {result.request_id}</p> : null}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
