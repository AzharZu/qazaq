/* eslint-disable @next/next/no-img-element */
import { useMemo, useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Flashcard from "./Flashcard";
import PronunciationRecorder from "./PronunciationRecorder";
import VideoPlayer from "./lesson/VideoPlayer";
import audioTaskApi from "@/lib/api/audioTask";
import { autocheckerApi, FreeWritingResponse } from "@/lib/api/autochecker";
import { LessonBlock, TheoryContent, FlashcardsContent, PronunciationContent, TasksContent } from "@/types/lesson";
import { resolveMediaUrl } from "@/lib/media";

type Props = {
  block: LessonBlock;
  lessonId: number;
  onComplete: () => void;
  preview?: boolean;
  onGoToStep?: (step: "theory" | "flashcards" | "pronunciation" | "tasks") => void;
  lessonLanguage?: string;
};

type ValidationResult<T> = { valid: true; value: T } | { valid: false; value: T };

const safeString = (value: any, fallback = ""): string => (typeof value === "string" ? value : fallback);
const resolveAudioSrc = (source: any): string => resolveMediaUrl(source?.audio_path || source?.audio_url || source?.url);

function AudioPlayer({ src }: { src: string }) {
  const [error, setError] = useState<string | null>(null);
  if (!src) return null;
  return (
    <div className="space-y-2">
      <audio
        controls
        src={src}
        className="w-full"
        onError={() => setError("Не удалось загрузить аудио. Проверьте ссылку или попробуйте позже.")}
      >
        Ваш браузер не поддерживает аудио.
      </audio>
      {error ? <div className="text-xs text-red-400">{error}</div> : null}
    </div>
  );
}

function validateTheory(raw: any): ValidationResult<TheoryContent> {
  const value: TheoryContent = {
    title: safeString(raw?.title),
    markdown: safeString(raw?.markdown || raw?.rich_text || raw?.text),
    rich_text: safeString(raw?.rich_text || raw?.markdown || raw?.text),
    video_url: safeString(raw?.video_url),
    thumbnail_url: safeString(raw?.thumbnail_url),
  };
  const hasMarkdown = Boolean(value.markdown && value.markdown.length > 0);
  const hasVideo = Boolean(value.video_url);
  return { valid: hasMarkdown || hasVideo, value };
}

function validateFlashcards(raw: any): ValidationResult<FlashcardsContent> {
  const cards = Array.isArray(raw?.cards || raw?.items)
    ? (raw.cards || raw.items).map((c: any, idx: number) => ({
        id: c?.id ?? idx,
        word: safeString(c?.word || c?.front),
        translation: safeString(c?.translation || c?.back),
        example_sentence: safeString(c?.example_sentence || c?.example),
        image_url: safeString(c?.image_url || c?.image || undefined, undefined),
        audio_path: safeString(c?.audio_path || c?.audio_url || ""),
        audio_url: safeString(c?.audio_url || c?.audio_path || ""),
      }))
    : [];
  return { valid: cards.length > 0, value: { cards } };
}

function validatePronunciation(raw: any): ValidationResult<PronunciationContent> {
  const items = Array.isArray(raw?.items || raw?.cards || raw?.words)
    ? (raw.items || raw.cards || raw.words).map((c: any, idx: number) => ({
        id: c?.id ?? idx,
        word: safeString(c?.word || c?.front),
        translation: safeString(c?.translation || c?.back),
        example: safeString(c?.example || c?.example_sentence),
        image_url: safeString(c?.image_url || c?.image || undefined, undefined),
        audio_path: safeString(c?.audio_path || c?.audio_url || ""),
        audio_url: safeString(c?.audio_url || c?.audio_path || ""),
      }))
    : [];
  return { valid: items.length > 0, value: { items, sample_audio_url: safeString(raw?.sample_audio_url) } };
}

function validateTasks(raw: any): ValidationResult<TasksContent> {
  const questions = Array.isArray(raw?.questions || raw?.tasks)
    ? (raw.questions || raw.tasks).map((q: any, idx: number) => ({
        id: q?.id ?? idx,
        question: safeString(q?.question, "Задание"),
        type: (safeString(q?.type, "single") as TasksContent["questions"][number]["type"]),
        options: Array.isArray(q?.options) ? q.options.map((o: any) => safeString(o)) : [],
        audio_path: safeString(q?.audio_path || q?.audio_url),
        audio_url: safeString(q?.audio_url || q?.audio_path),
        placeholder: safeString(q?.placeholder),
      }))
    : [];
  return { valid: questions.length > 0, value: { questions } };
}

export default function LessonBlockRenderer({ block, lessonId, onComplete, preview, onGoToStep, lessonLanguage }: Props) {
  const rawType = (
    block.type ||
    (block as any).block_type ||
    (block as any).blockType ||
    (block as any).kind ||
    (block as any).content?.type ||
    ""
  ) as string;
  const blockType = typeof rawType === "string" ? rawType.toLowerCase().replace(/-/g, "_") : "";
  useEffect(() => {
    console.debug("LessonBlockRenderer block type:", blockType, block);
  }, [blockType, block]);
  const supportedTypes = useMemo(
    () => [
      "video",
      "theory",
      "audio_theory",
      "image",
      "audio",
      "flashcards",
      "flashcard",
      "pronunciation",
      "audio_task",
      "audio-task",
      "lesson_test",
      "quiz",
      "theory_quiz",
      "test",
      "task",
      "free_writing",
    ],
    [],
  );
  const unsupported = !supportedTypes.includes(blockType);
  const content: any = useMemo(() => block.content ?? (block as any).data ?? block.payload ?? block, [block]);
  const [quizAnswer, setQuizAnswer] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [pronunciationProgress, setPronunciationProgress] = useState<Record<number, boolean>>({});
  const [pronunciationIndex, setPronunciationIndex] = useState(0);
  const [freeAnswer, setFreeAnswer] = useState("");
  const [freeResult, setFreeResult] = useState<FreeWritingResponse | null>(null);
  const [freeLoading, setFreeLoading] = useState(false);
  const [freeError, setFreeError] = useState<string | null>(null);
  useEffect(() => {
    setPronunciationProgress({});
    setPronunciationIndex(0);
  }, [block.id]);
  useEffect(() => {
    setFreeAnswer("");
    setFreeResult(null);
    setFreeError(null);
  }, [block.id, blockType]);
  useEffect(() => {
    if (unsupported && !preview) {
      onComplete();
    }
  }, [unsupported, preview, onComplete]);

  if (blockType === "video") {
    const videoUrl = safeString(content.video_url || content.url);
    const posterUrl = safeString(content.thumbnail_url);
    return (
      <div className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
        <VideoPlayer url={videoUrl} poster={posterUrl} />
        {content.caption && <p className="text-sm text-ink/80">{content.caption}</p>}
        <button
          className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
          type="button"
          onClick={onComplete}
        >
          Следующий блок
        </button>
      </div>
    );
  }

  if (blockType === "theory") {
    const theory = validateTheory(content);
    const data = theory.value;
    const hasVideo = Boolean(data.video_url);
    return (
      <div className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
        {hasVideo && (
          <VideoPlayer url={data.video_url} poster={data.thumbnail_url} />
        )}
        {data.title && <h3 className="text-xl font-semibold text-white">{data.title}</h3>}
        <div className="prose prose-invert max-w-none prose-headings:text-white prose-p:text-ink">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.rich_text || ""}</ReactMarkdown>
        </div>
        <button
          className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
          type="button"
          onClick={() => {
            onComplete();
            onGoToStep?.("flashcards");
          }}
        >
          Перейти к флеш-карточкам
        </button>
      </div>
    );
  }

  if (blockType === "audio_theory") {
    const audioUrl = resolveAudioSrc(content);
    return (
      <div className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
        {audioUrl ? <AudioPlayer src={audioUrl} /> : null}
        <div className="prose prose-invert max-w-none prose-headings:text-white prose-p:text-ink">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content.markdown || ""}</ReactMarkdown>
        </div>
        <button
          className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
          type="button"
          onClick={onComplete}
        >
          Далее
        </button>
      </div>
    );
  }

  if (blockType === "flashcards" || blockType === "flashcard") {
    const flashcards = validateFlashcards(content);
    const cards =
      flashcards.value.cards.length > 0
        ? flashcards.value.cards
        : Array.isArray(content.word_ids)
          ? content.word_ids.map((wid: number) => ({ id: wid, word: `Слово ${wid}`, translation: content.translation || "" }))
          : [];
    return (
      <Flashcard
        cards={cards}
        title={block.title || "Карточки"}
        onComplete={() => {
          onComplete();
          onGoToStep?.("pronunciation");
        }}
        ctaLabel="Перейти к произношению"
        onCta={() => {
          onComplete();
          onGoToStep?.("pronunciation");
        }}
      />
    );
  }

  if (blockType === "pronunciation") {
    const validation = validatePronunciation(content);
    const items = validation.value.items;
    const hasItems = Array.isArray(items) && items.length > 0;
    const active = hasItems ? items[Math.min(pronunciationIndex, items.length - 1)] : content;
    const word =
      active.word || active.title || active.phrase || active.expected_pronunciation || content.phrase || "Произнесите фразу";
    const wordId = active.word_id || active.id || content.word_id || block.word_id;
    const sampleAudio = resolveAudioSrc(active) || content.sample_audio_url;
    const doneCurrent = pronunciationProgress[pronunciationIndex];
    const allDone = hasItems ? items.every((_, idx) => pronunciationProgress[idx]) : doneCurrent;
    const playSample = () => {
      if (sampleAudio) {
        new Audio(sampleAudio).play();
      } else if (typeof window !== "undefined") {
        const utterance = new SpeechSynthesisUtterance(word);
        utterance.lang = "kk-KZ";
        window.speechSynthesis?.speak(utterance);
      }
    };
    return (
      <div className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-gold">Произнесите слово</p>
            <p className="text-3xl font-bold text-white">{word}</p>
            {hasItems ? <p className="text-xs text-ink/70">Слово {pronunciationIndex + 1} из {items.length}</p> : null}
          </div>
          <button
            type="button"
            onClick={playSample}
            className="rounded-xl bg-slate px-4 py-2 text-sm font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white"
          >
            Озвучить
          </button>
        </div>
        <PronunciationRecorder
          lessonId={lessonId}
          blockId={block.id}
          wordId={wordId || lessonId}
          word={word}
          sampleUrl={sampleAudio}
          preview={preview}
          onResult={() =>
            setPronunciationProgress((prev) => ({
              ...prev,
              [pronunciationIndex]: true,
            }))
          }
        />
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="flex-1 rounded-xl bg-slate px-5 py-3 text-sm font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white"
            onClick={() => {
              onComplete();
              onGoToStep?.("tasks");
            }}
          >
            Не могу говорить
          </button>
          <button
            type="button"
            onClick={() => {
              if (hasItems && pronunciationIndex + 1 < items.length) {
                setPronunciationIndex((idx) => idx + 1);
              } else {
                onComplete();
                onGoToStep?.("tasks");
              }
            }}
            className="flex-1 rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:bg-slate/50"
            disabled={hasItems && !doneCurrent && !preview}
          >
            {hasItems && pronunciationIndex + 1 < items.length ? "Следующее слово" : "Перейти к заданиям"}
          </button>
          {hasItems && pronunciationIndex > 0 ? (
            <button
              type="button"
              className="w-full rounded-xl bg-slate px-5 py-3 text-sm font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white"
              onClick={() => setPronunciationIndex((idx) => Math.max(idx - 1, 0))}
            >
              Назад к предыдущему слову
            </button>
          ) : null}
          {hasItems && allDone ? (
            <div className="w-full rounded-lg bg-slate/40 px-3 py-2 text-xs text-ink/80">
              Все слова проговорены, можно переходить дальше.
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  if (blockType === "audio_task" || blockType === "audio-task") {
    return <AudioTaskBlock block={block} content={content} onComplete={onComplete} />;
  }

  if (blockType === "audio") {
    const audioUrl = resolveAudioSrc(content) || resolveAudioSrc(block);
    const transcript = content.transcript || content.translation;
    return (
      <div className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
        {audioUrl ? <AudioPlayer src={audioUrl} /> : null}
        {transcript && <p className="text-sm text-ink/80">{transcript}</p>}
        <button
          type="button"
          onClick={onComplete}
          className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
        >
          Далее
        </button>
      </div>
    );
  }

  if (blockType === "image") {
    const imageUrl = content.image_url || block.image_url;
    const caption = content.explanation || content.caption || block.title;
    return (
      <div className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
        {imageUrl ? (
          <img src={imageUrl} alt={caption || "Изображение"} className="h-auto w-full rounded-xl object-cover" />
        ) : (
          <div className="flex h-64 items-center justify-center rounded-xl bg-slate/40 text-sm text-ink/70">Изображение недоступно</div>
        )}
        {caption && <p className="text-sm text-ink/80">{caption}</p>}
        <button
          type="button"
          onClick={onComplete}
          className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
        >
          Далее
        </button>
      </div>
    );
  }

  if (blockType === "free_writing") {
    const prompt = content.question || content.prompt || "Напишите небольшой ответ на задание.";
    const rubric = content.rubric || "";
    const language = (content.language || lessonLanguage || "kk") as string;

    const handleCheck = async () => {
      if (!freeAnswer.trim()) {
        setFreeError("Введите ответ для проверки.");
        return;
      }
      setFreeLoading(true);
      setFreeError(null);
      try {
        const res = await autocheckerApi.checkFreeWriting({
          prompt,
          student_answer: freeAnswer,
          rubric: rubric || undefined,
          language,
        });
        if (!res.ok) {
          setFreeResult(null);
          setFreeError(res.error || "Gemini недоступен. Попробуйте позже.");
        } else {
          setFreeResult(res);
        }
      } catch (err: any) {
        const data = err?.response?.data;
        const message = data?.error || data?.detail || err?.message || "Не удалось выполнить проверку.";
        setFreeResult(null);
        setFreeError(message);
      } finally {
        setFreeLoading(false);
      }
    };

    return (
      <div className="space-y-5 rounded-2xl bg-panel p-6 shadow-card">
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-wide text-gold">Free writing</p>
          <h3 className="text-2xl font-semibold text-white">{prompt}</h3>
          {rubric ? <p className="text-sm text-ink/80">Критерии: {rubric}</p> : null}
          <p className="text-xs text-ink/60">Язык проверки: {(language || "kk").toUpperCase()}</p>
        </div>

        <div className="space-y-3">
          <label className="text-sm font-semibold text-ink/80" htmlFor="free-writing-answer">
            Ваш ответ
          </label>
          <textarea
            id="free-writing-answer"
            rows={5}
            value={freeAnswer}
            onChange={(e) => setFreeAnswer(e.target.value)}
            className="w-full rounded-xl border border-slate/50 bg-midnight px-4 py-3 text-base text-ink shadow-inner placeholder:text-ink/50 focus:border-gold focus:outline-none"
            placeholder="Введите свободный ответ..."
          />
          <div className="flex flex-wrap items-center gap-3 text-xs text-ink/60">
            <span>Символов: {freeAnswer.length}</span>
            {freeResult?.request_id ? <span className="rounded bg-slate/50 px-2 py-1 font-mono text-[10px]">req {freeResult.request_id}</span> : null}
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={freeLoading || !freeAnswer.trim()}
            onClick={handleCheck}
            className="flex-1 rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:opacity-70"
          >
            {freeLoading ? "Проверяем..." : "Check"}
          </button>
          <button
            type="button"
            onClick={onComplete}
            className="rounded-xl bg-slate px-5 py-3 text-sm font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white"
          >
            {freeResult?.ok ? "Далее" : "Пропустить"}
          </button>
        </div>

        {freeError ? (
          <div className="rounded-xl border border-red-500/40 bg-red-900/40 px-4 py-3 text-sm text-red-100">{freeError}</div>
        ) : null}

        {freeResult?.ok ? (
          <div className="space-y-3 rounded-2xl border border-slate/50 bg-midnight/60 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <p className="text-sm uppercase tracking-wide text-gold">Результат</p>
                <p className="text-3xl font-semibold text-white">{freeResult.score ?? "—"}</p>
              </div>
              <div className="rounded-full bg-slate px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/80">
                {freeResult.level || "—"}
              </div>
            </div>
            <p className="text-sm text-ink/80">{freeResult.feedback || "Фидбек появится после проверки."}</p>
            {freeResult.corrections && freeResult.corrections.length ? (
              <ul className="space-y-2 text-sm text-ink">
                {freeResult.corrections.map((item, idx) => (
                  <li key={idx} className="flex gap-2">
                    <span className="mt-1 h-2 w-2 rounded-full bg-gold" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink/60">Исправления отсутствуют.</p>
            )}
            <div className="flex justify-end">
              <button
                type="button"
                onClick={onComplete}
                className="rounded-xl bg-gold px-5 py-2 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
              >
                Завершить блок
              </button>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  const tasksValidation = validateTasks(content);
  const questionsList = tasksValidation.value.questions.length ? tasksValidation.value.questions : content.questions || content.tasks;
  const isTasksBlock = ["quiz", "theory_quiz", "lesson_test", "test", "task"].includes(blockType);
  if (isTasksBlock) {
    if (Array.isArray(questionsList) && questionsList.length > 0) {
      const qs = tasksValidation.value.questions.length ? tasksValidation.value.questions : questionsList;
      return <QuizTasksBlock questions={qs} preview={preview} onComplete={onComplete} />;
    }
    return (
      <div className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
        <p className="text-sm font-semibold text-ink">Задания недоступны для этого блока.</p>
        {preview ? (
          <pre className="rounded bg-slate/40 p-3 text-xs text-ink/80 whitespace-pre-wrap">{JSON.stringify(content, null, 2)}</pre>
        ) : null}
        <button
          type="button"
          onClick={onComplete}
          className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
        >
          Продолжить
        </button>
      </div>
    );
  }

  console.warn("Unsupported block type", blockType, block);
  if (!preview) return null;
  return (
    <div className="rounded-2xl bg-panel p-6 shadow-card space-y-3">
      <p className="text-ink font-semibold">Блок недоступен: {blockType || "unknown"}</p>
      {preview ? (
        <pre className="rounded bg-slate/40 p-3 text-xs text-ink/80 whitespace-pre-wrap">{JSON.stringify(content, null, 2)}</pre>
      ) : null}
      <button
        className="mt-1 rounded-xl bg-gold px-4 py-2 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
        type="button"
        onClick={onComplete}
      >
        Продолжить
      </button>
    </div>
  );
}

function QuizTasksBlock({ questions, preview, onComplete }: { questions: any[]; preview?: boolean; onComplete: () => void }) {
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const updateAnswer = (idx: number, value: any) => setAnswers((prev) => ({ ...prev, [idx]: value }));
  return (
    <div className="space-y-6 rounded-2xl bg-panel p-6 shadow-card">
      <h3 className="text-2xl font-semibold text-white">Задания</h3>
      {questions.map((q, idx) => {
        const type = (q.type || "single").toLowerCase();
        const options = q.options || [];
        return (
          <div key={idx} className="space-y-3 rounded-2xl bg-midnight p-4 shadow-inner">
            <div className="flex items-center justify-between">
              <div className="text-base font-semibold text-white">
                {idx + 1}. {q.question || "Задание"}
              </div>
              <span className="rounded-full bg-slate px-3 py-1 text-xs font-semibold text-ink/80">{type}</span>
            </div>
            {type === "audio" || type === "audio_repeat" ? (
              <div className="flex items-center gap-3 rounded-xl bg-slate/60 p-3 text-sm text-ink/80">
                <button
                  type="button"
                  onClick={() => {
                    const src = resolveAudioSrc(q);
                    if (src) new Audio(src).play();
                  }}
                  className="rounded-full bg-gold px-4 py-2 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
                >
                  ▶ Слушать
                </button>
                <span>{q.prompt || "Прослушайте и повторите"}</span>
              </div>
            ) : null}
            {type === "single" || type === "single_choice" ? (
              <div className="space-y-2">
                {options.map((opt: string, optIdx: number) => (
                  <label
                    key={optIdx}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold shadow-soft transition ${
                      answers[idx] === optIdx ? "bg-gold text-slateDeep" : "bg-slate/60 text-ink hover:bg-slate"
                    }`}
                  >
                    <input
                      type="radio"
                      className="h-4 w-4"
                      checked={answers[idx] === optIdx}
                      disabled={preview}
                      onChange={() => updateAnswer(idx, optIdx)}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            ) : null}
            {type === "fill-in" ? (
              <input
                className="w-full rounded-xl bg-slate/60 px-4 py-3 text-sm text-ink placeholder:text-ink/50 shadow-inner focus:outline-none focus:ring-2 focus:ring-gold"
                placeholder={q.placeholder || "Введите ответ"}
                value={answers[idx] || ""}
                onChange={(e) => updateAnswer(idx, e.target.value)}
                disabled={preview}
              />
            ) : null}
            {type === "open" ? (
              <textarea
                className="w-full rounded-xl bg-slate/60 px-4 py-3 text-sm text-ink placeholder:text-ink/50 shadow-inner focus:outline-none focus:ring-2 focus:ring-gold"
                placeholder={q.placeholder || "Введите свободный ответ"}
                value={answers[idx] || ""}
                onChange={(e) => updateAnswer(idx, e.target.value)}
                disabled={preview}
                rows={3}
              />
            ) : null}
          </div>
        );
      })}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onComplete}
          className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
        >
          {preview ? "Закрыть предпросмотр" : "Продолжить"}
        </button>
      </div>
    </div>
  );
}

function AudioTaskBlock({ block, content, onComplete }: { block: LessonBlock; content: any; onComplete: () => void }) {
  const [answer, setAnswer] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [correct, setCorrect] = useState<boolean | null>(null);
  const options: string[] = content.options || [];
  const audioUrl = resolveAudioSrc(content);
  const transcript = content.transcript || content.prompt || content.question;

  const submit = async () => {
    setSubmitting(true);
    try {
      const res = await audioTaskApi.submit(block.id as number, {
        answer: answer || undefined,
        selected_option: selected ?? undefined,
      });
      setFeedback(res.feedback || (res.correct ? "Верно" : "Попробуйте ещё"));
      setCorrect(res.correct);
    } catch (err) {
      setFeedback("Не удалось отправить задание");
      setCorrect(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 rounded-2xl bg-panel p-6 shadow-card">
      <h3 className="text-2xl font-semibold text-white">Задания</h3>

      <div className="space-y-3 rounded-2xl bg-midnight p-5 shadow-inner">
        <p className="text-sm font-semibold uppercase tracking-wide text-gold">1. Прослушайте аудио и повторите</p>
        {audioUrl ? (
          <div className="space-y-2 rounded-xl bg-slate/60 p-4 shadow-inner">
            <div className="flex items-center gap-3 text-sm text-ink/80">
              <button
                type="button"
                onClick={() => new Audio(audioUrl).play()}
                className="rounded-full bg-gold px-4 py-2 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
              >
                ▶ Слушать
              </button>
              <span>{transcript || "Нажмите, чтобы прослушать фразу"}</span>
            </div>
            <AudioPlayer src={audioUrl} />
          </div>
        ) : (
          <div className="rounded-xl bg-slate/40 p-4 text-sm text-ink/60">Аудио не приложено</div>
        )}
        <div className="rounded-xl bg-slate/40 p-4 text-sm text-ink/70">Повторите вслух, затем переходите к ответу.</div>
      </div>

      <div className="space-y-3 rounded-2xl bg-midnight p-5 shadow-inner">
        <p className="text-sm font-semibold uppercase tracking-wide text-gold">
          {options.length > 0 ? "2. Выберите правильный вариант" : "2. Напишите, о чем говорится"}
        </p>
        {options.length > 0 ? (
          <div className="space-y-2">
            {options.map((opt, idx) => (
              <label
                key={idx}
                className={`flex cursor-pointer items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold shadow-soft transition ${
                  selected === idx ? "bg-gold text-slateDeep" : "bg-slate/60 text-ink hover:bg-slate"
                }`}
              >
                <input
                  type="radio"
                  className="h-4 w-4"
                  checked={selected === idx}
                  onChange={() => setSelected(idx)}
                />
                <span>{opt}</span>
              </label>
            ))}
          </div>
        ) : (
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            className="w-full rounded-xl bg-slate/60 px-4 py-3 text-sm text-ink placeholder:text-ink/50 shadow-inner focus:outline-none focus:ring-2 focus:ring-gold"
            placeholder="Прослушайте и напишите, о чем говорится"
            rows={4}
          />
        )}
      </div>

      {feedback && (
        <div className={`rounded-2xl px-4 py-3 text-sm font-semibold ${correct ? "bg-gold text-slateDeep" : "bg-red-500/30 text-white"}`}>
          {feedback}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          onClick={submit}
          disabled={submitting || (options.length > 0 && selected === null)}
          className="flex-1 rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:bg-slate/50"
        >
          {submitting ? "Отправляем..." : "Проверить"}
        </button>
        <button
          onClick={onComplete}
          className="flex-1 rounded-xl bg-slate px-5 py-3 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
        >
          Завершить
        </button>
      </div>
    </div>
  );
}
