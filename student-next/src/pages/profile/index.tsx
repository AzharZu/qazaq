import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import ProgressBar from "@/components/ProgressBar";
import { playDictionaryAudio } from "@/lib/useDictionaryWords";
import dictionaryApi, { DictionaryStats } from "@/lib/api/dictionary";
import { CourseService } from "@/services/CourseService";
import { ProgressService } from "@/services/ProgressService";
import { useAuthStore } from "@/store/authStore";
import { useDictionaryStore } from "@/store/dictionaryStore";
import { Course } from "@/types/course";
import { ProgressResponse } from "@/types/progress";
import { VocabularyWord } from "@/types/vocabulary";

const formatNumber = (value: number) => {
  if (Number.isNaN(value)) return "0";
  return value.toLocaleString("ru-RU");
};

export default function ProfilePage() {
  const { user, token, loadUser, loading: authLoading } = useAuthStore();
  const { words, loadWords, markSuccess } = useDictionaryStore();
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [dictionaryStats, setDictionaryStats] = useState<DictionaryStats | null>(null);
  const [wordOfWeek, setWordOfWeek] = useState<VocabularyWord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingWord, setSavingWord] = useState(false);

  useEffect(() => {
    if (!user && token && !authLoading) {
      loadUser();
    }
  }, [authLoading, loadUser, token, user]);

  useEffect(() => {
    if (!token) return;
    loadWords().catch(() => {});
  }, [token, loadWords]);

  useEffect(() => {
    if (!token) return;
    let active = true;

    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        const [progressPayload, coursesRes, stats, weeklyWord] = await Promise.all([
          ProgressService.overview(),
          CourseService.list(),
          dictionaryApi.getStats(),
          dictionaryApi.getWordOfWeek(),
        ]);
        if (!active) return;
        setProgress(progressPayload);
        setCourses(coursesRes?.courses || []);
        setDictionaryStats(stats || {});
        setWordOfWeek(weeklyWord);
      } catch (err: any) {
        if (!active) return;
        const message = err?.response?.data?.detail || "Не удалось загрузить профиль";
        setError(message);
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchAll();
    return () => {
      active = false;
    };
  }, [token]);

  const currentCourse = useMemo(() => {
    if (!courses.length) return null;
    if (progress?.course_id) {
      const found = courses.find((c) => c.id === progress.course_id);
      if (found) return found;
    }
    if (progress?.course_slug) {
      const found = courses.find((c) => c.slug === progress.course_slug);
      if (found) return found;
    }
    return courses[0];
  }, [courses, progress]);

  const progressMap = useMemo(() => currentCourse?.progress_map || {}, [currentCourse]);

  const completedModules = useMemo(
    () =>
      (currentCourse?.modules || [])
        .filter((module) => {
          const lessons = module.lessons || [];
          if (!lessons.length) return false;
          return lessons.every((lesson) => {
            const status = progressMap?.[lesson.id] ?? progressMap?.[String(lesson.id)];
            return status === "done";
          });
        })
        .map((module) => ({ id: module.id, name: module.name, order: module.order }))
        .sort((a, b) => (a.order || 0) - (b.order || 0) || a.id - b.id),
    [currentCourse?.modules, progressMap]
  );

  const completedLessons = useMemo(
    () =>
      (currentCourse?.modules || [])
        .flatMap((module) =>
          (module.lessons || []).map((lesson) => ({
            id: lesson.id,
            title: lesson.title,
            order: lesson.order,
            moduleOrder: module.order || 0,
            status: progressMap?.[lesson.id] ?? progressMap?.[String(lesson.id)],
          }))
        )
        .filter((lesson) => lesson.status === "done")
        .sort((a, b) => a.moduleOrder - b.moduleOrder || a.order - b.order || a.id - b.id),
    [currentCourse?.modules, progressMap]
  );

  const learnedWordsCount = useMemo(() => {
    if (dictionaryStats && typeof dictionaryStats.learned === "number") return dictionaryStats.learned;
    return words.filter((w) => w.status === "learned" || w.learned).length;
  }, [dictionaryStats, words]);

  const displayName = user?.name || (user?.email ? user.email.split("@")[0] : "—");
  const displayEmail = user?.email || "—";
  const streakDays = progress?.streak_days || 0;
  const dailyTarget = progress?.goal_today?.target || user?.daily_minutes || 0;
  const usedMinutes = progress?.goal_today?.completed ? dailyTarget : progress?.xp_today || 0;
  const minutesLeft = Math.max(0, dailyTarget - usedMinutes);
  const courseTitle = progress?.course_title || currentCourse?.name || "—";
  const levelLabel = user?.level || "—";
  const percentValue = progress?.percent || 0;
  const lessonsDone = progress?.completed_lessons || completedLessons.length;
  const lessonsTotal = progress?.total_lessons || (currentCourse?.modules || []).reduce((acc, m) => acc + (m.lessons?.length || 0), 0);

  const highlightedWord = useMemo(() => {
    const weekly = wordOfWeek && wordOfWeek.word ? wordOfWeek : null;
    if (weekly) {
      const match = words.find((w) => (w.word || "").toLowerCase() === (weekly.word || "").toLowerCase());
      if (match) return match as VocabularyWord;
      return weekly;
    }
    return words.length ? (words[0] as VocabularyWord) : null;
  }, [wordOfWeek, words]);

  const wordAlreadyInDictionary = highlightedWord ? words.some((w) => w.id === highlightedWord.id) : false;

  const handleSpeakWord = () => {
    if (!highlightedWord) return;
    playDictionaryAudio({
      id: highlightedWord.id,
      wordKz: highlightedWord.word || "",
      translationRu: highlightedWord.translation || "",
      audioUrl: highlightedWord.audio_url || undefined,
    });
  };

  const handleAddWord = async () => {
    if (!highlightedWord || !wordAlreadyInDictionary || !highlightedWord.id) return;
    setSavingWord(true);
    try {
      await markSuccess(Number(highlightedWord.id));
      await loadWords();
      const refreshed = await dictionaryApi.getStats();
      setDictionaryStats(refreshed);
    } catch (err: any) {
      const message = err?.response?.data?.detail || "Не удалось обновить словарь";
      setError(message);
    } finally {
      setSavingWord(false);
    }
  };

  if (!token && authLoading) {
    return <div className="card-surface p-8">Загружаем профиль...</div>;
  }

  if (!token) {
    return (
      <div className="card-surface p-8 text-center">
        <p className="text-sm text-ink/80">Войдите, чтобы просмотреть профиль.</p>
        <div className="mt-4 flex justify-center">
          <Link
            href="/login"
            className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
          >
            Войти
          </Link>
        </div>
      </div>
    );
  }

  if (loading && !progress) {
    return <div className="card-surface p-8">Загружаем профиль...</div>;
  }

  return (
    <div className="space-y-10">
      <div className="card-surface flex flex-col items-center gap-4 p-8 text-center">
        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-slate text-3xl text-ink/60 shadow-soft">
          <span className="select-none">👤</span>
        </div>
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-white md:text-3xl">{displayName}</h1>
          <p className="text-sm text-ink/70">{displayEmail}</p>
        </div>
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            className="rounded-lg bg-slate px-4 py-2 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
          >
            Мои сертификаты
          </button>
          <button
            type="button"
            className="rounded-lg bg-slate px-4 py-2 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
          >
            Настройки
          </button>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="card-surface p-5">
          <p className="text-sm text-ink/70">Дней подряд</p>
          <div className="text-3xl font-bold text-gold">{formatNumber(streakDays)}</div>
        </div>
        <div className="card-surface p-5">
          <p className="text-sm text-ink/70">Слов выучено</p>
          <div className="text-3xl font-bold text-gold">{formatNumber(learnedWordsCount)}</div>
        </div>
        <div className="card-surface p-5">
          <p className="text-sm text-ink/70">Осталось минут сегодня</p>
          <div className="text-3xl font-bold text-gold">{formatNumber(minutesLeft)}</div>
        </div>
      </div>

      <div className="card-surface space-y-4 p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-gold">Текущий прогресс обучения</p>
            <h2 className="text-xl font-semibold text-white">{courseTitle}</h2>
            <p className="text-sm text-ink/70">Уровень: {levelLabel}</p>
          </div>
          <span className="rounded-full bg-slate px-4 py-2 text-sm font-semibold text-gold">{percentValue}%</span>
        </div>
        <ProgressBar value={percentValue} />
        <p className="text-sm text-ink/80">
          Пройдено уроков: {lessonsDone} из {lessonsTotal}
        </p>
      </div>

      <div className="card-surface space-y-5 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold text-white">Слово недели</h3>
          {highlightedWord?.word && <span className="text-xs uppercase tracking-wide text-gold">Из словаря</span>}
        </div>
        <div className="space-y-2 text-center">
          <div className="text-4xl font-bold text-gold md:text-5xl">{highlightedWord?.word || "—"}</div>
          <div className="text-sm text-ink/70">{highlightedWord?.translation || "Нет перевода"}</div>
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={handleSpeakWord}
            className="rounded-lg bg-slate px-4 py-2 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
            disabled={!highlightedWord}
          >
            Озвучить
          </button>
          <button
            type="button"
            onClick={handleAddWord}
            disabled={!wordAlreadyInDictionary || savingWord}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              wordAlreadyInDictionary
                ? "bg-gold text-slateDeep shadow-soft hover:bg-goldDark disabled:opacity-70"
                : "bg-slate/50 text-ink/60"
            }`}
          >
            {wordAlreadyInDictionary ? (savingWord ? "Добавляем..." : "Добавить в словарь") : "Нет в словаре"}
          </button>
          <Link
            href="/dictionary"
            className="rounded-lg bg-slate px-4 py-2 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
          >
            Мой словарь
          </Link>
        </div>
      </div>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-white">История обучения</h2>

        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-white">Пройденные модули</h3>
          <div className="card-surface space-y-3 p-4">
            {completedModules.length ? (
              completedModules.map((module) => (
                <div key={module.id} className="rounded-lg bg-slate/40 px-4 py-3 text-ink">
                  <p className="text-sm font-semibold text-white">
                    Модуль {module.order}: {module.name}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-ink/60">Завершенные модули появятся здесь после прохождения уроков.</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-white">Пройденные уроки</h3>
          <div className="card-surface space-y-3 p-4">
            {completedLessons.length ? (
              completedLessons.map((lesson) => (
                <div key={lesson.id} className="rounded-lg bg-slate/40 px-4 py-3 text-ink">
                  <p className="text-sm font-semibold text-white">
                    Урок {lesson.order} — {lesson.title}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-ink/60">После завершения уроков они появятся в истории.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
