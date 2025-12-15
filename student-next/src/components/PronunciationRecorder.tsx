import { useEffect, useRef, useState } from "react";
import client from "@/lib/api/client";

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
};

export default function PronunciationRecorder({ lessonId, blockId, word, sampleUrl, onDone, onResult, wordId, preview, disabled }: Props) {
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState<"idle" | "recording" | "uploading" | "done" | "error">("idle");
  const [score, setScore] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [resultTone, setResultTone] = useState<"excellent" | "good" | "ok" | "bad" | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  useEffect(() => {
    return () => stopRecording(true);
  }, []);

  const startRecording = async () => {
    if (preview || disabled) {
      setMessage("Preview: запись отключена для этого режима");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await uploadRecording(blob);
        cleanupStream();
        setRecording(false);
      };

      recorder.start();
      setStatus("recording");
      setRecording(true);
      setMessage("Говорите чётко, запись идёт...");
    } catch (err) {
      console.error(err);
      setStatus("error");
      setMessage("Не удалось начать запись. Разрешите доступ к микрофону.");
    }
  };

  const stopRecording = (silent?: boolean) => {
    if (!recorderRef.current) return;
    if (!silent) setStatus("uploading");
    recorderRef.current.stop();
    recorderRef.current = null;
  };

  const cleanupStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
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

  const uploadRecording = async (blob: Blob) => {
    if (preview || disabled) {
      setStatus("done");
      setMessage("Preview: отправка отключена");
      return;
    }
    setStatus("uploading");
    setMessage("Сравниваем произношение...");
    try {
      const formData = new FormData();
      formData.append("audio", blob, "audio.webm");
      if (wordId) formData.append("word_id", String(wordId));
      if (word) formData.append("target_text", word);
      if (lessonId) formData.append("lesson_id", String(lessonId));
      if (blockId) formData.append("block_id", String(blockId));

      const { data } = await client.post<{ score?: number; status?: "excellent" | "good" | "ok" | "bad"; feedback?: string }>(
        "/pronunciation/check",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      const value = typeof data.score === "number" ? data.score : 0;
      const normalizedStatus: "excellent" | "good" | "ok" | "bad" =
        data.status || (value > 0.75 ? "excellent" : value > 0.5 ? "ok" : "bad");
      setScore(value);
      setResultTone(normalizedStatus);
      onDone?.(value);
      onResult?.(value, normalizedStatus);
      setStatus("done");
      setMessage(
        data.feedback ||
          (normalizedStatus === "excellent"
            ? "Отлично сказано!"
            : normalizedStatus === "ok" || normalizedStatus === "good"
            ? "Неплохо, попробуйте ещё"
            : "Попробуйте произнести четче"),
      );
    } catch (err) {
      console.error(err);
      setStatus("error");
      setMessage("Не удалось отправить запись");
    }
  };

  const scoreTone =
    resultTone === "excellent"
      ? "bg-green-200/60 text-green-900"
      : resultTone === "good" || resultTone === "ok"
      ? "bg-yellow-200/60 text-yellow-900"
      : resultTone === "bad"
      ? "bg-red-400/40 text-white"
      : "bg-slate/40 text-ink";

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
          {status === "recording" && <span className="text-xs font-semibold text-gold">Запись...</span>}
          {status === "uploading" && <span className="text-xs font-semibold text-gold">Обрабатываем...</span>}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {!recording ? (
            <button
              type="button"
              onClick={startRecording}
              className="flex-1 rounded-xl bg-slate px-5 py-3 text-sm font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white"
            >
              Записать голос
            </button>
          ) : (
            <button
              type="button"
              onClick={() => stopRecording()}
              className="flex-1 rounded-xl bg-red-500 px-5 py-3 text-sm font-semibold text-white shadow-soft transition hover:bg-red-600"
            >
              Остановить
            </button>
          )}
          <div className={`rounded-xl px-4 py-2 text-xs font-semibold ${scoreTone}`}>
            {resultTone ? (resultTone === "excellent" ? "Excellent" : resultTone === "good" ? "Good" : "Try again") : "Оценка"}
          </div>
        </div>
        {message && <div className="rounded-lg bg-midnight/40 px-3 py-2 text-sm text-ink/80">{message}</div>}
      </div>
    </div>
  );
}
