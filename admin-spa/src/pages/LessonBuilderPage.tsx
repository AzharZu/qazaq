import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { lessonBuilderApi } from "../api/lessonBuilder";
import { BlockType, Lesson, LessonBlock } from "../types";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardTitle } from "../components/ui/card";
import { useToast } from "../components/ui/use-toast";
import { Spinner } from "../components/ui/spinner";
import { VideoPlayer } from "../components/ui/video-player";
import { resolveMediaUrl } from "../lib/media";

type EditorProps = {
  block: LessonBlock;
  onChange: (content: Record<string, any>) => void;
  onUpload: (kind: "image" | "audio" | "video", file: File, field?: string) => Promise<{ url: string; thumbnail_url?: string }>;
};

const BLOCK_TEMPLATES: Record<BlockType, Record<string, any>> = {
  video: { video_url: "", thumbnail_url: "", caption: "" },
  theory: { title: "", markdown: "", video_url: "", thumbnail_url: "" },
  audio_theory: { audio_path: "", audio_url: "", markdown: "" },
  image: { image_url: "", explanation: "", keywords: [] },
  audio: { audio_path: "", audio_url: "", transcript: "", translation: "" },
  flashcards: { cards: [] },
  pronunciation: { items: [] },
  theory_quiz: { question: "", type: "single", options: ["", ""], correct_answer: [], explanation: "" },
  quiz: { title: "", questions: [] },
  audio_task: { audio_path: "", audio_url: "", transcript: "", options: ["", ""], correct_answer: "", answer_type: "multiple_choice", feedback: "" },
  lesson_test: { passing_score: 80, questions: [{ question: "", type: "single", options: ["", ""], correct_answer: [] }] },
  free_writing: { question: "", rubric: "", language: "kk" },
};

const typeLabels: Record<BlockType, string> = {
  video: "Video",
  theory: "Theory",
  audio_theory: "Audio + Theory",
  image: "Image",
  audio: "Audio",
  flashcards: "Flashcards",
  pronunciation: "Pronunciation",
  audio_task: "Audio Task",
  theory_quiz: "Theory Quiz",
  quiz: "Quiz",
  lesson_test: "Final Test",
  free_writing: "Free writing",
};

function deepCopy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value));
}

function SectionLabel({ children }: { children: string }) {
  return <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{children}</div>;
}

const CANONICAL_ORDER = ["theory", "flashcards", "pronunciation", "quiz", "theory_quiz", "lesson_test", "free_writing"];

function sortBlocksCanonical(blocks: LessonBlock[]): LessonBlock[] {
  return [...blocks].sort((a, b) => {
    const aIdx = CANONICAL_ORDER.indexOf(a.type);
    const bIdx = CANONICAL_ORDER.indexOf(b.type);
    if (aIdx !== -1 && bIdx !== -1 && aIdx !== bIdx) return aIdx - bIdx;
    if (aIdx !== -1 && bIdx === -1) return -1;
    if (aIdx === -1 && bIdx !== -1) return 1;
    return (a.order || 0) - (b.order || 0);
  });
}

type FlashcardRow = {
  id?: number | string;
  word: string;
  translation: string;
  example_sentence?: string;
  image_url?: string;
  audio_path?: string;
  audio_url?: string;
  order?: number;
};

type TaskQuestion = {
  id?: number | string;
  question: string;
  type: string;
  options?: string[];
  correct_answer?: string | string[] | number | number[];
  audio_path?: string;
  audio_url?: string;
  placeholder?: string;
};

function extractFlashcardsFromBlock(block: LessonBlock | null): FlashcardRow[] {
  if (!block) return [];
  const content = (block.content || block.data || {}) as Record<string, any>;
  const cards: any[] = content.cards || content.items || [];
  return cards.map((card, idx) => ({
    id: card.id ?? idx,
    word: card.word || card.front || "",
    translation: card.translation || card.back || "",
    example_sentence: card.example_sentence || card.example || "",
    image_url: card.image_url || card.image,
    audio_path: card.audio_path,
    audio_url: card.audio_url,
    order: card.order || idx + 1,
  }));
}

export default function LessonBuilderPage() {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [blocks, setBlocks] = useState<LessonBlock[]>([]);
  const [loading, setLoading] = useState(false);
  const [pendingLessonPatch, setPendingLessonPatch] = useState<Partial<Lesson>>({});
  const [pendingBlocks, setPendingBlocks] = useState<Map<number, Partial<LessonBlock>>>(new Map());
  const [pendingReorder, setPendingReorder] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [normalized, setNormalized] = useState(false);
  const { toast } = useToast();
  const studentAppBase = (import.meta.env.VITE_STUDENT_URL || import.meta.env.VITE_STUDENT_APP_URL || "http://localhost:3002").replace(/\/$/, "");

  const theoryBlock = useMemo(() => blocks.find((b) => b.type === "theory") || null, [blocks]);
  const flashcardsBlock = useMemo(() => blocks.find((b) => b.type === "flashcards") || null, [blocks]);
  const pronunciationBlock = useMemo(() => blocks.find((b) => b.type === "pronunciation") || null, [blocks]);
  const quizBlock = useMemo(
    () => blocks.find((b) => b.type === "quiz" || b.type === "lesson_test" || b.type === "theory_quiz") || null,
    [blocks],
  );
  const freeWritingBlock = useMemo(() => blocks.find((b) => b.type === "free_writing") || null, [blocks]);
  const legacyBlocks = useMemo(
    () =>
      blocks.filter(
        (b) => !["theory", "flashcards", "pronunciation", "quiz", "lesson_test", "theory_quiz", "free_writing"].includes(b.type),
      ),
    [blocks],
  );

  const loadLesson = useCallback(async () => {
    if (!lessonId) return;
    setLoading(true);
    try {
      const data = await lessonBuilderApi.fetchLesson(Number(lessonId));
      setLesson(data);
      setBlocks(sortBlocksCanonical(data.blocks || []).map((b, idx) => ({ ...b, order: idx + 1 })));
      setPendingLessonPatch({});
      setPendingBlocks(new Map());
      setPendingReorder(false);
      setDirty(false);
      setNormalized(false);
    } catch (err: any) {
      toast({ title: "Failed to load lesson", description: err?.message || "Error", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    loadLesson();
  }, [loadLesson]);

  useEffect(() => {
    if (!flashcardsBlock || !pronunciationBlock) return;
    const cards = extractFlashcardsFromBlock(flashcardsBlock);
    const current = (pronunciationBlock.content || pronunciationBlock.data || {}) as any;
    const nextContent = { ...current, items: cards };
    const prevJson = JSON.stringify(current.items || []);
    const nextJson = JSON.stringify(cards);
    if (prevJson !== nextJson) {
      handleBlockChange(pronunciationBlock.id, nextContent);
    }
  }, [flashcardsBlock, pronunciationBlock]);

  useEffect(() => {
    if (!lesson || normalized) return;
    const ensureCanonical = async () => {
      if (!lesson) return;
      let nextBlocks = [...blocks];
      const maybeCreate = async (type: BlockType) => {
        const existing = nextBlocks.find((b) => b.type === type);
        if (existing) return existing;
        const created = await lessonBuilderApi.createBlock(lesson.id, { type, content: deepCopy(BLOCK_TEMPLATES[type]) });
        nextBlocks = [...nextBlocks, created];
        return created;
      };
      await maybeCreate("theory");
      await maybeCreate("flashcards");
      await maybeCreate("pronunciation");
      await maybeCreate("quiz");
      await maybeCreate("free_writing");
      const sorted = sortBlocksCanonical(nextBlocks).map((b, idx) => ({ ...b, order: idx + 1 }));
      setBlocks(sorted);
      setPendingReorder(true);
      setDirty(true);
      setNormalized(true);
    };
    ensureCanonical();
  }, [lesson, blocks, normalized]);

  const handleLessonChange = (patch: Partial<Lesson>) => {
    setLesson((prev) => (prev ? { ...prev, ...patch } : prev));
    setPendingLessonPatch((prev) => ({ ...prev, ...patch }));
    setDirty(true);
  };

  const handleBlockChange = (blockId: number, content: Record<string, any>) => {
    setBlocks((prev) => prev.map((b) => (b.id === blockId ? { ...b, content, data: content } : b)));
    setPendingBlocks((prev) => {
      const next = new Map(prev);
      next.set(blockId, { content, data: content });
      return next;
    });
    setDirty(true);
  };

  const flushChanges = useCallback(async () => {
    if (!lesson) return;
    if (!dirty) return;
    setSaving(true);
    try {
      if (Object.keys(pendingLessonPatch).length) {
        await lessonBuilderApi.updateLesson(lesson.id, pendingLessonPatch);
        setPendingLessonPatch({});
      }
      for (const [blockId, patch] of pendingBlocks.entries()) {
        await lessonBuilderApi.updateBlock(blockId, { content: patch.content as any });
      }
      if (pendingBlocks.size) setPendingBlocks(new Map());
      if (pendingReorder) {
        const order = blocks.map((b) => b.id);
        await lessonBuilderApi.reorderBlocks(lesson.id, order);
        setPendingReorder(false);
      }
      setDirty(false);
    } catch (err: any) {
      toast({ title: "Autosave failed", description: err?.message || "Error", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }, [lesson, dirty, pendingLessonPatch, pendingBlocks, pendingReorder, blocks, toast]);

  useEffect(() => {
    if (!dirty) return;
    const timer = setTimeout(() => {
      flushChanges();
    }, 500);
    return () => clearTimeout(timer);
  }, [dirty, flushChanges]);

  const handleDeleteBlock = async (blockId: number) => {
    try {
      await lessonBuilderApi.deleteBlock(blockId);
      setBlocks((prev) => prev.filter((b) => b.id !== blockId));
      setPendingBlocks((prev) => {
        const next = new Map(prev);
        next.delete(blockId);
        return next;
      });
      setPendingReorder(true);
      setDirty(true);
    } catch (err: any) {
      toast({ title: "Delete failed", description: err?.message || "Error", variant: "destructive" });
    }
  };

  const handleDuplicateBlock = async (blockId: number) => {
    try {
      const clone = await lessonBuilderApi.duplicateBlock(blockId);
      setBlocks((prev) => {
        const idx = prev.findIndex((b) => b.id === blockId);
        const next = [...prev];
        next.splice(idx + 1, 0, clone);
        return next.map((b, i) => ({ ...b, order: i + 1 }));
      });
      setPendingReorder(true);
      setDirty(true);
    } catch (err: any) {
      toast({ title: "Duplicate failed", description: err?.message || "Error", variant: "destructive" });
    }
  };

  const handleUpload = async (kind: "image" | "audio" | "video", file: File) => {
    const resp = await lessonBuilderApi.upload(kind, file);
    return resp;
  };

  const updateFlashcards = (nextCards: FlashcardRow[]) => {
    if (!flashcardsBlock) return;
    const normalizedCards = nextCards.map((card, idx) => ({ ...card, order: idx + 1 }));
    handleBlockChange(flashcardsBlock.id, { ...(flashcardsBlock.content || flashcardsBlock.data || {}), cards: normalizedCards });
  };

  const updateTasks = (nextQuestions: TaskQuestion[]) => {
    if (!quizBlock) return;
    handleBlockChange(quizBlock.id, { ...(quizBlock.content || quizBlock.data || {}), questions: nextQuestions });
  };

  const heroPrimary = lesson?.title || "Lesson";
  const flashcardRows = extractFlashcardsFromBlock(flashcardsBlock);
  const taskQuestions: TaskQuestion[] = ((quizBlock?.content || quizBlock?.data || {}) as any).questions || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <SectionLabel>Lesson Builder</SectionLabel>
          <h1 className="text-2xl font-bold text-slate-900">{heroPrimary}</h1>
          <p className="text-sm text-slate-600">
            Канонические секции: теория → флеш-карточки → произношение → задания. Все сохраняется автоматически.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/admin/lessons" className="rounded-md border border-border bg-white px-3 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50">
            Back to lessons
          </Link>
          {lesson ? (
            <>
              <Button
                variant="outline"
                onClick={() => window.open(`${studentAppBase}/lesson/${lesson.id}?preview=1`, "_blank")}
              >
                Preview
              </Button>
              <Button
                variant="outline"
                onClick={async () => {
                  const updated = await lessonBuilderApi.updateLesson(lesson.id, { status: "draft" });
                  setLesson((prev) => (prev ? { ...prev, ...updated } : updated));
                  toast({ title: "Unpublished", description: "Lesson set to draft" });
                }}
              >
                Unpublish
              </Button>
              <Button
                onClick={async () => {
                  const updated = await lessonBuilderApi.publishLesson(lesson.id);
                  setLesson((prev) => (prev ? { ...prev, ...updated } : updated));
                  toast({ title: "Published", description: "Lesson marked as published" });
                }}
              >
                Publish
              </Button>
              <Button variant="outline" onClick={flushChanges} disabled={saving}>
                {saving ? "Saving..." : "Save now"}
              </Button>
            </>
          ) : null}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600">
          <Spinner /> Loading lesson...
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        <Card className="bg-white shadow-sm">
          <CardContent className="space-y-3 p-4">
            <div className="flex items-center justify-between">
              <CardTitle>Metadata</CardTitle>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setPreviewOpen((v) => !v)}>
                  {previewOpen ? "Hide preview" : "Preview"}
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <a href={`${studentAppBase}/lesson/${lesson?.id}?preview=1`} target="_blank" rel="noreferrer">
                    Open in student
                  </a>
                </Button>
              </div>
            </div>
            <Input
              placeholder="Title"
              value={lesson?.title || ""}
              onChange={(e) => handleLessonChange({ title: e.target.value })}
            />
            <Textarea
              placeholder="Short description"
              value={lesson?.description || ""}
              onChange={(e) => handleLessonChange({ description: e.target.value })}
              rows={3}
            />
            <div className="grid grid-cols-2 gap-2">
              <Input
                placeholder="Difficulty"
                value={lesson?.difficulty || ""}
                onChange={(e) => handleLessonChange({ difficulty: e.target.value })}
              />
              <Input
                placeholder="Language"
                value={lesson?.language || ""}
                onChange={(e) => handleLessonChange({ language: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Input
                placeholder="Estimated time (min)"
                type="number"
                value={lesson?.estimated_time ?? ""}
                onChange={(e) => handleLessonChange({ estimated_time: Number(e.target.value || 0) })}
              />
              <Input
                placeholder="Status"
                value={lesson?.status || ""}
                onChange={(e) => handleLessonChange({ status: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-600">Video type</label>
                <select
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                  value={lesson?.video_type || "youtube"}
                  onChange={(e) => handleLessonChange({ video_type: e.target.value })}
                >
                  <option value="youtube">YouTube</option>
                  <option value="vimeo">Vimeo</option>
                  <option value="file">Self-hosted mp4</option>
                </select>
                <Input
                  placeholder="Video URL"
                  value={lesson?.video_url || ""}
                  onChange={(e) => handleLessonChange({ video_url: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-600">Preview</label>
                <VideoPlayer videoType={(lesson?.video_type || "youtube").toLowerCase()} videoUrl={lesson?.video_url || ""} height="180px" />
              </div>
            </div>
            <div className="text-xs text-slate-500">
              {saving ? "Saving…" : dirty ? "Pending changes" : "Saved"}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="bg-white shadow-sm">
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <CardTitle>📘 Теория</CardTitle>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="rounded-full bg-slate-100 px-2 py-1">Видео опционально</span>
                  <span className="rounded-full bg-slate-100 px-2 py-1">Текст обязателен</span>
                </div>
              </div>
              {theoryBlock ? (
                <>
                  <Input
                    placeholder="Video URL"
                    value={(theoryBlock.content?.video_url as string) || ""}
                    onChange={(e) =>
                      handleBlockChange(theoryBlock.id, { ...(theoryBlock.content || {}), video_url: e.target.value })
                    }
                  />
                  <Textarea
                    placeholder="Markdown / текст теории"
                    rows={8}
                    value={(theoryBlock.content?.markdown as string) || (theoryBlock.content?.rich_text as string) || ""}
                    onChange={(e) =>
                      handleBlockChange(theoryBlock.id, {
                        ...(theoryBlock.content || {}),
                        markdown: e.target.value,
                        rich_text: e.target.value,
                      })
                    }
                  />
                </>
              ) : (
                <div className="text-sm text-slate-600">Блок теории создается автоматически.</div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm">
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <CardTitle>🧠 Флеш-карточки</CardTitle>
                <div className="text-xs text-slate-500">{flashcardRows.length} cards</div>
              </div>
              <p className="text-sm text-slate-600">Слова используются далее в произношении и заданиях.</p>
              <FlashcardsTable cards={flashcardRows} onChange={updateFlashcards} onUpload={handleUpload} />
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm">
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <CardTitle>🎙 Произношение</CardTitle>
                <span className="text-xs text-slate-500">Автогенерация из карточек, только чтение</span>
              </div>
              <p className="text-sm text-slate-600">
                Эти элементы появятся на student-site: прослушать образец, записать голос, получить feedback.
              </p>
              <PronunciationReadonly items={flashcardRows} />
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm">
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <CardTitle>📝 Задания / тест</CardTitle>
                <span className="text-xs text-slate-500">Порядок важен</span>
              </div>
              <TasksEditor questions={taskQuestions} onChange={updateTasks} onUpload={handleUpload} />
            </CardContent>
          </Card>

          {freeWritingBlock ? (
            <Card className="bg-white shadow-sm">
              <CardContent className="space-y-3 p-4">
                <div className="flex items-center justify-between">
                  <CardTitle>✍️ Free writing</CardTitle>
                  <span className="text-xs text-slate-500">Gemini check</span>
                </div>
                <p className="text-sm text-slate-600">Финальный блок: студент пишет ответ, Gemini возвращает оценку/фидбек.</p>
                <FreeWritingEditor
                  content={freeWritingBlock.content || freeWritingBlock.data || {}}
                  onChange={(content) => handleBlockChange(freeWritingBlock.id, content)}
                />
              </CardContent>
            </Card>
          ) : null}

          {legacyBlocks.length ? (
            <Card className="bg-white shadow-sm">
              <CardContent className="space-y-3 p-4">
                <div className="flex items-center justify-between">
                  <CardTitle>Legacy blocks</CardTitle>
                  <span className="text-xs text-slate-500">для обратной совместимости</span>
                </div>
                <div className="space-y-3">
                  {legacyBlocks.map((block) => (
                    <div key={block.id} className="rounded-lg border border-slate-200 p-3">
                      <div className="mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                            {typeLabels[block.type]}
                          </span>
                          <span className="text-xs text-slate-500">#{block.order}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button size="sm" variant="outline" onClick={() => handleDuplicateBlock(block.id)}>
                            Duplicate
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => handleDeleteBlock(block.id)}>
                            Delete
                          </Button>
                        </div>
                      </div>
                      <BlockEditor
                        block={block}
                        onChange={(content) => handleBlockChange(block.id, content)}
                        onUpload={(kind, file) => handleUpload(kind, file)}
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : null}

          {previewOpen ? (
            <Card className="bg-white shadow-sm">
              <CardContent className="space-y-4 p-4">
                <div className="flex items-center justify-between">
                  <CardTitle>Preview</CardTitle>
                  <div className="text-xs text-slate-500">{blocks.length} blocks</div>
                </div>
                <LessonPreview lesson={lesson} blocks={blocks} studentUrl={`${studentAppBase}/lesson/${lesson?.id}?preview=1`} />
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function FlashcardsTable({
  cards,
  onChange,
  onUpload,
}: {
  cards: FlashcardRow[];
  onChange: (cards: FlashcardRow[]) => void;
  onUpload: EditorProps["onUpload"];
}) {
  const [uploadingIdx, setUploadingIdx] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const updateField = (idx: number, field: keyof FlashcardRow, value: string) => {
    const next = [...cards];
    next[idx] = { ...next[idx], [field]: value };
    onChange(next);
  };

  const handleAudioUpload = (idx: number, file: File) => {
    setUploadError(null);
    setUploadingIdx(idx);
    onUpload("audio", file)
      .then((resp) => {
        const raw = resp.url || "";
        const resolved = resolveMediaUrl(raw);
        updateField(idx, "audio_path", raw);
        updateField(idx, "audio_url", raw);
        try {
          const audio = new Audio(resolved);
          audio.play().catch(() => {});
        } catch {
          // ignore autoplay errors
        }
      })
      .catch((err: any) => {
        setUploadError(err?.response?.data?.detail || err?.message || "Не удалось загрузить аудио");
      })
      .finally(() => setUploadingIdx(null));
  };

  return (
    <div className="space-y-3">
      {cards.map((card, idx) => (
        <div key={card.id ?? idx} className="space-y-2 rounded-lg border border-slate-200 p-3">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>#{idx + 1}</span>
            <Button variant="ghost" size="sm" onClick={() => onChange(cards.filter((_, i) => i !== idx))}>
              Remove
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Input
              placeholder="Word"
              value={card.word}
              onChange={(e) => updateField(idx, "word", e.target.value)}
            />
            <Input
              placeholder="Translation"
              value={card.translation}
              onChange={(e) => updateField(idx, "translation", e.target.value)}
            />
          </div>
          <Textarea
            placeholder="Example sentence"
            rows={2}
            value={card.example_sentence || ""}
            onChange={(e) => updateField(idx, "example_sentence", e.target.value)}
          />
          <div className="grid grid-cols-2 gap-2">
            <Input
              placeholder="Image URL"
              value={card.image_url || ""}
              onChange={(e) => updateField(idx, "image_url", e.target.value)}
            />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <input
                  type="file"
                  accept="audio/mpeg,audio/mp3,audio/wav,audio/ogg,audio/webm"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleAudioUpload(idx, file);
                  }}
                />
                {uploadingIdx === idx ? <span className="text-xs text-slate-500">Загружаю...</span> : null}
              </div>
              {(card.audio_path || card.audio_url) && (
                <audio
                  controls
                  src={resolveMediaUrl(card.audio_path || card.audio_url || "")}
                  className="w-full"
                />
              )}
            </div>
          </div>
        </div>
      ))}
      <Button
        variant="outline"
        onClick={() =>
          onChange([
            ...cards,
            { word: "", translation: "", example_sentence: "", image_url: "", audio_path: "", audio_url: "", id: `new-${Date.now()}` },
          ])
        }
      >
        + Добавить слово
      </Button>
      {uploadError ? <div className="text-xs text-red-500">{uploadError}</div> : null}
    </div>
  );
}

function PronunciationReadonly({ items }: { items: FlashcardRow[] }) {
  if (!items.length) {
    return <div className="rounded-lg border border-dashed border-slate-300 p-3 text-sm text-slate-600">Нет слов для произношения.</div>;
  }
  return (
    <div className="space-y-2">
      {items.map((item, idx) => (
        <div key={item.id ?? idx} className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div>
            <div className="text-sm font-semibold text-slate-900">{item.word}</div>
            <div className="text-xs text-slate-600">{item.translation}</div>
            {item.example_sentence ? <div className="text-xs text-slate-500">{item.example_sentence}</div> : null}
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            {(item.audio_path || item.audio_url) ? <span>🎧</span> : null}
            {item.image_url ? <span>🖼</span> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

function TasksEditor({
  questions,
  onChange,
  onUpload,
}: {
  questions: TaskQuestion[];
  onChange: (questions: TaskQuestion[]) => void;
  onUpload: EditorProps["onUpload"];
}) {
  const [uploadingIdx, setUploadingIdx] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const addQuestion = (type: string) => {
    const template: TaskQuestion = { question: "", type, options: type === "single" ? ["", ""] : [], correct_answer: [] };
    if (type === "audio_repeat") template.options = [];
    if (type === "fill-in") template.correct_answer = "";
    if (type === "open") template.correct_answer = "";
    onChange([...(questions || []), template]);
  };
  const updateQuestion = (idx: number, patch: Partial<TaskQuestion>) => {
    const next = [...questions];
    next[idx] = { ...next[idx], ...patch };
    onChange(next);
  };
  const removeQuestion = (idx: number) => onChange(questions.filter((_, i) => i !== idx));

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={() => addQuestion("audio_repeat")}>
          + Audio listening
        </Button>
        <Button variant="outline" size="sm" onClick={() => addQuestion("single")}>
          + Single choice
        </Button>
        <Button variant="outline" size="sm" onClick={() => addQuestion("fill-in")}>
          + Fill in the blank
        </Button>
        <Button variant="outline" size="sm" onClick={() => addQuestion("open")}>
          + Free writing
        </Button>
      </div>
      {questions.map((q, idx) => {
        const type = (q.type || "single").toLowerCase();
        const options = q.options || [];
        return (
          <div key={idx} className="space-y-2 rounded-lg border border-slate-200 p-3">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-slate-100 px-2 py-1">{type}</span>
                <span>#{idx + 1}</span>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => removeQuestion(idx)}>
                  Remove
                </Button>
              </div>
            </div>
            <Input
              placeholder="Вопрос / инструкция"
              value={q.question}
              onChange={(e) => updateQuestion(idx, { question: e.target.value })}
            />
            {type === "audio_repeat" ? (
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="file"
                    accept="audio/mpeg,audio/mp3,audio/wav,audio/ogg,audio/webm"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      setUploadError(null);
                      setUploadingIdx(idx);
                      onUpload("audio", file)
                        .then((resp) => {
                          const raw = resp.url || "";
                          const resolved = resolveMediaUrl(raw);
                          updateQuestion(idx, { audio_path: raw, audio_url: raw });
                          try {
                            const audio = new Audio(resolved);
                            audio.play().catch(() => {});
                          } catch {
                            // ignore autoplay errors
                          }
                        })
                        .catch((err: any) => setUploadError(err?.response?.data?.detail || err?.message || "Не удалось загрузить аудио"))
                        .finally(() => setUploadingIdx(null));
                    }}
                  />
                  {uploadingIdx === idx ? <span className="text-xs text-slate-500">Загружаю...</span> : null}
                </div>
                {(q.audio_path || q.audio_url) && (
                  <audio controls src={resolveMediaUrl(q.audio_path || q.audio_url || "")} className="w-full">
                    Ваш браузер не поддерживает аудио.
                  </audio>
                )}
              </div>
            ) : null}
            {type === "single" ? (
              <div className="space-y-2">
                {options.map((opt, optIdx) => (
                  <div key={optIdx} className="flex items-center gap-2">
                    <Input
                      value={opt}
                      onChange={(e) => {
                        const next = [...options];
                        next[optIdx] = e.target.value;
                        updateQuestion(idx, { options: next });
                      }}
                    />
                    <label className="flex items-center gap-1 text-xs text-slate-600">
                      <input
                        type="radio"
                        checked={q.correct_answer === optIdx || (Array.isArray(q.correct_answer) && q.correct_answer?.[0] === optIdx)}
                        onChange={() => updateQuestion(idx, { correct_answer: optIdx })}
                      />
                      Correct
                    </label>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => updateQuestion(idx, { options: [...options, ""] })}
                >
                  + Add option
                </Button>
              </div>
            ) : null}
            {type === "fill-in" ? (
              <Input
                placeholder="Correct answer"
                value={(q.correct_answer as string) || ""}
                onChange={(e) => updateQuestion(idx, { correct_answer: e.target.value })}
              />
            ) : null}
            {type === "open" ? (
              <Textarea
                placeholder="Подсказка для ученика"
                rows={3}
                value={q.placeholder || ""}
                onChange={(e) => updateQuestion(idx, { placeholder: e.target.value })}
              />
            ) : null}
          </div>
        );
      })}
      {uploadError ? <div className="text-xs text-red-500">{uploadError}</div> : null}
    </div>
  );
}

function LessonPreview({ lesson, blocks, studentUrl }: { lesson: Lesson | null; blocks: LessonBlock[]; studentUrl: string }) {
  const ordered = useMemo(() => [...blocks].sort((a, b) => a.order - b.order), [blocks]);
  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="space-y-1">
        <div className="text-lg font-semibold text-slate-900">{lesson?.title || "Untitled lesson"}</div>
        <div className="text-sm text-slate-600">{lesson?.description}</div>
      </div>
      <div className="space-y-2">
        {ordered.map((block) => (
          <PreviewBlock key={block.id} block={block} />
        ))}
      </div>
      {lesson?.id ? (
        <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
          <iframe title="Student preview" src={studentUrl} className="h-[640px] w-full border-0" />
        </div>
      ) : null}
    </div>
  );
}

function PreviewBlock({ block }: { block: LessonBlock }) {
  const content = block.content || block.data || {};
  const titleMap: Record<string, string> = {
    video: "Video",
    theory: "Theory",
    audio_theory: "Audio + Theory",
    flashcards: "Flashcards",
    pronunciation: "Pronunciation",
    theory_quiz: "Quiz",
    quiz: "Quiz",
    audio_task: "Audio Task",
    lesson_test: "Lesson Test",
    free_writing: "Free writing",
  };
  return (
    <div className="rounded-lg bg-white p-3 shadow-inner">
      <div className="mb-1 text-sm font-semibold text-slate-700 flex items-center justify-between">
        <span>{titleMap[block.type] || "Block"}</span>
        <span className="text-xs text-slate-500">#{block.order}</span>
      </div>
      <pre className="whitespace-pre-wrap text-xs text-slate-600">
        {JSON.stringify(content, null, 2)}
      </pre>
    </div>
  );
}

function BlockEditor({ block, onChange, onUpload }: EditorProps) {
  const content = block.content || block.data || {};
  if (block.type === "video") return <VideoEditor content={content} onChange={onChange} onUpload={onUpload} />;
  if (block.type === "theory") return <TheoryEditor content={content} onChange={onChange} />;
  if (block.type === "audio_theory") return <AudioTheoryEditor content={content} onChange={onChange} onUpload={onUpload} />;
  if (block.type === "image") return <ImageEditor content={content} onChange={onChange} onUpload={onUpload} />;
  if (block.type === "audio") return <AudioEditor content={content} onChange={onChange} onUpload={onUpload} />;
  if (block.type === "flashcards") return <FlashcardEditor content={content} onChange={onChange} onUpload={onUpload} />;
  if (block.type === "pronunciation") return <PronunciationEditor content={content} onChange={onChange} onUpload={onUpload} />;
  if (block.type === "audio_task") return <AudioTaskEditor content={content} onChange={onChange} onUpload={onUpload} />;
  if (block.type === "theory_quiz" || block.type === "quiz") return <QuizEditor content={content} onChange={onChange} />;
  if (block.type === "lesson_test") return <TestEditor content={content} onChange={onChange} />;
  if (block.type === "free_writing") return <FreeWritingEditor content={content} onChange={onChange} />;
  return <div className="text-sm text-slate-500">Unsupported block</div>;
}

function VideoEditor({ content, onChange, onUpload }: { content: Record<string, any>; onChange: (c: Record<string, any>) => void; onUpload: EditorProps["onUpload"] }) {
  return (
    <div className="space-y-3">
      <Input
        placeholder="Video URL"
        value={content.video_url || content.url || ""}
        onChange={(e) => onChange({ ...content, video_url: e.target.value, url: e.target.value })}
      />
      <div className="flex items-center gap-2">
        <Input
          placeholder="Thumbnail URL"
          value={content.thumbnail_url || ""}
          onChange={(e) => onChange({ ...content, thumbnail_url: e.target.value })}
        />
      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file)
            onUpload("image", file).then((resp) =>
              onChange({ ...content, thumbnail_url: resp.thumbnail_url || resp.url || content.thumbnail_url }),
            );
        }}
      />
      </div>
      <Textarea
        placeholder="Caption"
        value={content.caption || ""}
        onChange={(e) => onChange({ ...content, caption: e.target.value })}
      />
      <div className="flex items-center gap-2">
        <input
        type="file"
        accept="video/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file)
            onUpload("video", file).then((resp) =>
              onChange({
                ...content,
                video_url: resp.url || content.video_url,
                thumbnail_url: resp.thumbnail_url || content.thumbnail_url,
              }),
            );
        }}
      />
        <span className="text-xs text-slate-500">Upload video to storage</span>
      </div>
    </div>
  );
}

function TheoryEditor({ content, onChange }: { content: Record<string, any>; onChange: (c: Record<string, any>) => void }) {
  return (
    <div className="space-y-3">
      <Textarea
        placeholder="Markdown"
        rows={6}
        value={content.markdown || content.text || content.rich_text || ""}
        onChange={(e) => onChange({ ...content, markdown: e.target.value })}
      />
    </div>
  );
}

function AudioTheoryEditor({
  content,
  onChange,
  onUpload,
}: {
  content: Record<string, any>;
  onChange: (c: Record<string, any>) => void;
  onUpload: EditorProps["onUpload"];
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (file: File) => {
    setError(null);
    setUploading(true);
    onUpload("audio", file)
      .then((resp) => {
        const raw = resp.url || "";
        const resolved = resolveMediaUrl(raw);
        onChange({ ...content, audio_path: raw, audio_url: raw });
        try {
          new Audio(resolved).play().catch(() => {});
        } catch {
          /* ignore */
        }
      })
      .catch((err: any) => setError(err?.response?.data?.detail || err?.message || "Не удалось загрузить аудио"))
      .finally(() => setUploading(false));
  };

  return (
    <div className="space-y-3">
      <input
        type="file"
        accept="audio/mpeg,audio/mp3,audio/wav,audio/ogg,audio/webm"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {uploading ? <div className="text-xs text-slate-500">Загружаю...</div> : null}
      {error ? <div className="text-xs text-red-500">{error}</div> : null}
      {(content.audio_path || content.audio_url) && (
        <audio controls src={resolveMediaUrl(content.audio_path || content.audio_url)} className="w-full">
          Ваш браузер не поддерживает аудио.
        </audio>
      )}
      <Textarea
        placeholder="Markdown"
        rows={6}
        value={content.markdown || ""}
        onChange={(e) => onChange({ ...content, markdown: e.target.value })}
      />
    </div>
  );
}

function ImageEditor({
  content,
  onChange,
  onUpload,
}: {
  content: Record<string, any>;
  onChange: (c: Record<string, any>) => void;
  onUpload: EditorProps["onUpload"];
}) {
  const keywords: string[] = content.keywords || [];
  return (
    <div className="space-y-3">
      <Input
        placeholder="Image URL"
        value={content.image_url || ""}
        onChange={(e) => onChange({ ...content, image_url: e.target.value })}
      />
      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUpload("image", file).then((resp) => onChange({ ...content, image_url: resp.url || content.image_url }));
        }}
      />
      <Textarea
        placeholder="Explanation"
        rows={3}
        value={content.explanation || ""}
        onChange={(e) => onChange({ ...content, explanation: e.target.value })}
      />
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-600">Keywords</div>
        {keywords.map((word, idx) => (
          <Input
            key={idx}
            value={word}
            onChange={(e) => {
              const next = [...keywords];
              next[idx] = e.target.value;
              onChange({ ...content, keywords: next });
            }}
          />
        ))}
        <Button variant="outline" size="sm" onClick={() => onChange({ ...content, keywords: [...keywords, ""] })}>
          + Add keyword
        </Button>
      </div>
    </div>
  );
}

function AudioEditor({
  content,
  onChange,
  onUpload,
}: {
  content: Record<string, any>;
  onChange: (c: Record<string, any>) => void;
  onUpload: EditorProps["onUpload"];
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (file: File) => {
    setError(null);
    setUploading(true);
    onUpload("audio", file)
      .then((resp) => {
        const raw = resp.url || "";
        const resolved = resolveMediaUrl(raw);
        onChange({ ...content, audio_path: raw, audio_url: raw });
        try {
          new Audio(resolved).play().catch(() => {});
        } catch {
          /* ignore */
        }
      })
      .catch((err: any) => setError(err?.response?.data?.detail || err?.message || "Не удалось загрузить аудио"))
      .finally(() => setUploading(false));
  };

  return (
    <div className="space-y-3">
      <input
        type="file"
        accept="audio/mpeg,audio/mp3,audio/wav,audio/ogg,audio/webm"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {uploading ? <div className="text-xs text-slate-500">Загружаю...</div> : null}
      {error ? <div className="text-xs text-red-500">{error}</div> : null}
      {(content.audio_path || content.audio_url) && (
        <audio controls src={resolveMediaUrl(content.audio_path || content.audio_url)} className="w-full">
          Ваш браузер не поддерживает аудио.
        </audio>
      )}
      <Textarea
        placeholder="Transcript"
        rows={3}
        value={content.transcript || ""}
        onChange={(e) => onChange({ ...content, transcript: e.target.value })}
      />
      <Textarea
        placeholder="Translation"
        rows={2}
        value={content.translation || ""}
        onChange={(e) => onChange({ ...content, translation: e.target.value })}
      />
    </div>
  );
}

function FreeWritingEditor({ content, onChange }: { content: Record<string, any>; onChange: (c: Record<string, any>) => void }) {
  return (
    <div className="space-y-3">
      <Input
        placeholder="Вопрос / задание"
        value={content.question || ""}
        onChange={(e) => onChange({ ...content, question: e.target.value })}
      />
      <Textarea
        placeholder="Критерии / rubric (опционально)"
        rows={3}
        value={content.rubric || ""}
        onChange={(e) => onChange({ ...content, rubric: e.target.value })}
      />
      <div className="flex items-center gap-3">
        <label className="text-xs font-semibold text-slate-600">Язык проверки</label>
        <select
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm"
          value={content.language || "kk"}
          onChange={(e) => onChange({ ...content, language: e.target.value })}
        >
          <option value="kk">Kazakh (kk)</option>
          <option value="ru">Russian (ru)</option>
          <option value="en">English (en)</option>
        </select>
      </div>
    </div>
  );
}

function FlashcardEditor({
  content,
  onChange,
}: {
  content: Record<string, any>;
  onChange: (c: Record<string, any>) => void;
}) {
  const wordIds: (number | string)[] = content.word_ids || [];
  return (
    <div className="space-y-3">
      <Textarea
        placeholder="Word IDs (comma separated)"
        value={wordIds.join(",")}
        onChange={(e) => {
          const next = e.target.value
            .split(",")
            .map((v) => v.trim())
            .filter((v) => v.length);
          onChange({ ...content, word_ids: next });
        }}
      />
      <p className="text-xs text-slate-500">Укажите ID слов из словаря, которые будут в карточках.</p>
    </div>
  );
}

function PronunciationEditor({
  content,
  onChange,
}: {
  content: Record<string, any>;
  onChange: (c: Record<string, any>) => void;
}) {
  return (
    <div className="space-y-3">
      <Input
        placeholder="Word ID"
        value={content.word_id || ""}
        onChange={(e) => onChange({ ...content, word_id: e.target.value })}
      />
      <Textarea
        placeholder="Target text"
        rows={3}
        value={content.target_text || ""}
        onChange={(e) => onChange({ ...content, target_text: e.target.value })}
      />
    </div>
  );
}

function QuizEditor({ content, onChange }: { content: Record<string, any>; onChange: (c: Record<string, any>) => void }) {
  const options: string[] = content.options || [];
  const correctIndex = content.correct_index ?? 0;
  return (
    <div className="space-y-2">
      <Input
        placeholder="Question"
        value={content.question || ""}
        onChange={(e) => onChange({ ...content, question: e.target.value })}
      />
      <Input
        placeholder="Explanation"
        value={content.explanation || ""}
        onChange={(e) => onChange({ ...content, explanation: e.target.value })}
      />
      <div className="space-y-2">
        {options.map((opt, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <Input
              value={opt}
              onChange={(e) => {
                const next = [...options];
                next[idx] = e.target.value;
                onChange({ ...content, options: next });
              }}
            />
            <label className="flex items-center gap-1 text-xs text-slate-600">
              <input
                type="radio"
                checked={Number(correctIndex) === idx}
                onChange={() => onChange({ ...content, correct_index: idx })}
              />
              Correct
            </label>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={() => onChange({ ...content, options: [...options, ""] })}>
          + Add option
        </Button>
      </div>
    </div>
  );
}

function TestEditor({ content, onChange }: { content: Record<string, any>; onChange: (c: Record<string, any>) => void }) {
  const questions: any[] = content.questions || [];
  return (
    <div className="space-y-3">
      <Input
        type="number"
        placeholder="Passing score"
        value={content.passing_score || 0}
        onChange={(e) => onChange({ ...content, passing_score: Number(e.target.value) })}
      />
      {questions.map((q, idx) => (
        <div key={idx} className="rounded-lg border border-slate-100 p-3 shadow-inner">
          <Input
            placeholder="Question"
            value={q.question || ""}
            onChange={(e) => {
              const next = [...questions];
              next[idx] = { ...q, question: e.target.value };
              onChange({ ...content, questions: next });
            }}
          />
          <div className="mt-2 grid grid-cols-2 gap-2">
            <select
              className="rounded-md border border-slate-200 px-2 py-1 text-sm"
              value={q.type || "single"}
              onChange={(e) => {
                const next = [...questions];
                next[idx] = { ...q, type: e.target.value };
                onChange({ ...content, questions: next });
              }}
            >
              <option value="single">Single</option>
              <option value="multiple">Multiple</option>
              <option value="fill-in">Fill in</option>
            </select>
            <div className="text-xs text-slate-600">Supports audio/image references.</div>
          </div>
          <div className="mt-2 space-y-2">
            {(q.options || []).map((opt: string, optIdx: number) => (
              <Input
                key={optIdx}
                value={opt}
                onChange={(e) => {
                  const nextOptions = [...(q.options || [])];
                  nextOptions[optIdx] = e.target.value;
                  const next = [...questions];
                  next[idx] = { ...q, options: nextOptions };
                  onChange({ ...content, questions: next });
                }}
              />
            ))}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const next = [...questions];
                next[idx] = { ...q, options: [...(q.options || []), ""] };
                onChange({ ...content, questions: next });
              }}
            >
              + Add option
            </Button>
          </div>
          <Input
            className="mt-2"
            placeholder="Correct answer (text or CSV for multiple)"
            value={Array.isArray(q.correct_answer) ? q.correct_answer.join(",") : q.correct_answer || ""}
            onChange={(e) => {
              const value = e.target.value;
              const normalized =
                (q.type || "single") === "multiple" ? value.split(",").map((v: string) => v.trim()) : value;
              const next = [...questions];
              next[idx] = { ...q, correct_answer: normalized };
              onChange({ ...content, questions: next });
            }}
          />
          <div className="mt-2 grid grid-cols-2 gap-2">
            <Input
              placeholder="Audio URL"
              value={q.audio_url || ""}
              onChange={(e) => {
                const next = [...questions];
                next[idx] = { ...q, audio_url: e.target.value };
                onChange({ ...content, questions: next });
              }}
            />
            <Input
              placeholder="Image URL"
              value={q.image_url || ""}
              onChange={(e) => {
                const next = [...questions];
                next[idx] = { ...q, image_url: e.target.value };
                onChange({ ...content, questions: next });
              }}
            />
          </div>
        </div>
      ))}
      <Button
        variant="outline"
        size="sm"
        onClick={() => onChange({ ...content, questions: [...questions, deepCopy(BLOCK_TEMPLATES.lesson_test.questions[0])] })}
      >
        + Add question
      </Button>
    </div>
  );
}

function AudioTaskEditor({
  content,
  onChange,
  onUpload,
}: {
  content: Record<string, any>;
  onChange: (c: Record<string, any>) => void;
  onUpload: EditorProps["onUpload"];
}) {
  const options: string[] = content.options || [];
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (file: File) => {
    setError(null);
    setUploading(true);
    onUpload("audio", file)
      .then((resp) => {
        const raw = resp.url || "";
        const resolved = resolveMediaUrl(raw);
        onChange({ ...content, audio_path: raw, audio_url: raw });
        try {
          new Audio(resolved).play().catch(() => {});
        } catch {
          /* ignore */
        }
      })
      .catch((err: any) => setError(err?.response?.data?.detail || err?.message || "Не удалось загрузить аудио"))
      .finally(() => setUploading(false));
  };

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <input
          type="file"
          accept="audio/mpeg,audio/mp3,audio/wav,audio/ogg,audio/webm"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        {uploading ? <div className="text-xs text-slate-500">Загружаю...</div> : null}
        {error ? <div className="text-xs text-red-500">{error}</div> : null}
        {(content.audio_path || content.audio_url) && (
          <audio controls src={resolveMediaUrl(content.audio_path || content.audio_url)} className="w-full">
            Ваш браузер не поддерживает аудио.
          </audio>
        )}
      </div>
      <Textarea
        placeholder="Transcript"
        rows={3}
        value={content.transcript || ""}
        onChange={(e) => onChange({ ...content, transcript: e.target.value })}
      />
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-600">Options (leave empty for free-text)</div>
        {options.map((opt, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <Input
              value={opt}
              onChange={(e) => {
                const next = [...options];
                next[idx] = e.target.value;
                onChange({ ...content, options: next });
              }}
            />
            <label className="flex items-center gap-1 text-xs text-slate-600">
              <input
                type="radio"
                checked={content.correct_answer === opt}
                onChange={() => onChange({ ...content, correct_answer: opt })}
              />
              Correct
            </label>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={() => onChange({ ...content, options: [...options, ""] })}>
          + Add option
        </Button>
      </div>
      <Input
        placeholder="Correct answer (text fallback)"
        value={content.correct_answer || ""}
        onChange={(e) => onChange({ ...content, correct_answer: e.target.value })}
      />
      <Input
        placeholder="Feedback"
        value={content.feedback || ""}
        onChange={(e) => onChange({ ...content, feedback: e.target.value })}
      />
      <select
        className="rounded-md border border-slate-200 px-2 py-1 text-sm"
        value={content.answer_type || (options.length ? "multiple_choice" : "text")}
        onChange={(e) => onChange({ ...content, answer_type: e.target.value })}
      >
        <option value="multiple_choice">Multiple choice</option>
        <option value="text">Text</option>
      </select>
    </div>
  );
}
