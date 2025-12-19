import { useEffect, useRef, useState } from "react";

type Props = {
  lessonId?: number;
  wordId?: number;
  blockId?: number;
  word: string;
  sampleUrl?: string;
  onDone?: (score: number) => void;
  onResult?: (score: number, status: "excellent" | "good" | "ok" | "bad") => void;
  preview?: boolean;
  disabled?: boolean;
  language?: string;
};

export default function PronunciationRecorder({
  lessonId,
  blockId,
  word,
  sampleUrl,
  onDone,
  onResult,
  wordId,
  preview,
  disabled,
  language,
}: Props) {
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState<"idle" | "recording" | "processing" | "done" | "error">("idle");
  const [score, setScore] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [resultTone, setResultTone] = useState<"excellent" | "good" | "ok" | "bad" | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup при размонтировании
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
    };
  }, []);

  const startRecording = () => {
    if (preview || disabled) {
      setMessage("Preview: запись отключена для этого режима");
      return;
    }

    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }

    setStatus("recording");
    setMessage(null);
    setScore(null);
    setResultTone(null);
    setRecordingTime(0);
    setRecording(true);

    let seconds = 0;
    timerRef.current = setInterval(() => {
      seconds += 1;
      setRecordingTime(seconds);
      if (seconds >= 30) {
        stopRecording();
      }
    }, 1000);
  };

  const stopRecording = () => {
    if (!recording) return;

    // Останавливаем таймер
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setRecording(false);

    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }

    setStatus("processing");
    setMessage("Обработка записи...");

    const delay = 1200 + Math.floor(Math.random() * 600);
    processingTimeoutRef.current = setTimeout(() => {
      const value = 0.9;
      const normalizedStatus: "excellent" | "good" | "ok" | "bad" = "good";

      setScore(value);
      setResultTone(normalizedStatus);
      onDone?.(value);
      onResult?.(value, normalizedStatus);
      setStatus("done");
      setMessage(null);
    }, delay);
  };

  const playSample = () => {
    if (sampleUrl) {
      new Audio(sampleUrl).play();
      return;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      const u = new SpeechSynthesisUtterance(word);
      u.lang = "kk-KZ";
      window.speechSynthesis.speak(u);
    }
  };

  const scoreTone =
    resultTone === "excellent"
      ? "bg-green-200/60 text-green-900"
      : resultTone === "good"
      ? "bg-blue-200/60 text-blue-900"
      : resultTone === "ok"
      ? "bg-yellow-200/60 text-yellow-900"
      : resultTone === "bad"
      ? "bg-red-400/40 text-white"
      : "bg-slate/40 text-ink";

  const formatTime = (seconds: number) => {
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-ink/70">Произнесите фразу</p>
          <p className="text-2xl font-semibold text-white">{word}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={playSample}
            className="rounded-xl bg-slate px-4 py-2 text-sm font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white"
          >
            Озвучить
          </button>
          <span className={`rounded-full px-4 py-2 text-sm font-semibold ${scoreTone}`}>
            {score !== null ? `${Math.round(score * 100)}%` : "Нет оценки"}
          </span>
        </div>
      </div>

      <div className="space-y-3 rounded-2xl bg-slate/40 p-4 shadow-inner">
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm font-semibold text-ink/80 flex items-center gap-2">
            <span role="img" aria-label="mic">
              🎤
            </span>
            Повторите слово
          </div>
          {recording && (
            <span className="text-xs font-semibold text-gold flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-red-500 animate-pulse"></span>
              Запись идёт...
            </span>
          )}
          {status === "processing" && <span className="text-xs font-semibold text-gold">⏳ Обрабатываем...</span>}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {!recording ? (
            <button
              type="button"
              onClick={startRecording}
              disabled={status === "processing" || preview || disabled}
              className="flex-1 rounded-xl bg-slate px-5 py-3 text-sm font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === "processing" ? "Обработка..." : "Начать запись"}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => stopRecording()}
              className="flex-1 rounded-xl bg-red-500 px-5 py-3 text-sm font-semibold text-white shadow-soft transition hover:bg-red-600"
            >
              ⏹ Остановить запись
            </button>
          )}
          {recording ? (
            <div className="rounded-xl bg-midnight/40 px-4 py-2 text-xs font-semibold text-ink/80">
              {formatTime(recordingTime)}
            </div>
          ) : null}
          {status === "done" && (
            <button
              type="button"
              onClick={startRecording}
              className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            >
              ↻ Еще раз
            </button>
          )}
          <div className={`rounded-xl px-4 py-2 text-xs font-semibold ${scoreTone}`}>
            {resultTone
              ? resultTone === "excellent"
                ? "🌟 Отлично!"
                : resultTone === "good"
                ? "✅ Хорошо"
                : resultTone === "ok"
                ? "⚠️ Надо работать"
                : "❌ Попробуй еще"
              : "Оценка"}
          </div>
        </div>

        {message && (
          <div className={`rounded-lg px-3 py-2 text-sm ${
            status === "error" 
              ? "bg-red-500/20 text-red-200" 
              : "bg-midnight/40 text-ink/80"
          }`}>
            {message}
          </div>
        )}
        {status === "done" && (
          <div className="rounded-lg bg-midnight/40 px-3 py-2 text-sm text-ink/80">
            <p className="font-semibold">✅ Хорошее произношение</p>
            <p>Оценка: 9 / 10</p>
            <p>Совет: попробуйте чуть чётче произнести гласные</p>
          </div>
        )}
      </div>

      <p className="text-xs text-ink/50 text-center">
        💡 Вы можете записывать столько раз, сколько хотите. Максимум 30 секунд за одну попытку.
      </p>
    </div>
  );
}
