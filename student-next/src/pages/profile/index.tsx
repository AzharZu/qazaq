import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import ProgressBar from "@/components/ProgressBar";
import certificatesApi, { CertificateStatus } from "@/lib/api/certificates";
import dictionaryApi, { DictionaryStats } from "@/lib/api/dictionary";
import usersApi from "@/lib/api/users";
import { playDictionaryAudio } from "@/lib/useDictionaryWords";
import { CourseService } from "@/services/CourseService";
import { ProgressService } from "@/services/ProgressService";
import { useAuthStore } from "@/store/authStore";
import { useDictionaryStore } from "@/store/dictionaryStore";
import { Course } from "@/types/course";
import { ProgressResponse } from "@/types/progress";
import { User } from "@/types/user";
import { VocabularyWord } from "@/types/vocabulary";

const formatNumber = (value: number) => {
  if (Number.isNaN(value)) return "0";
  return value.toLocaleString("ru-RU");
};

const extractError = (err: any, fallback: string) => {
  const detail = err?.response?.data?.detail;
  if (Array.isArray(detail)) return detail[0] || fallback;
  if (typeof detail === "string") return detail;
  return fallback;
};

export default function ProfilePage() {
  const { user, token, loadUser, setUser, loading: authLoading } = useAuthStore();
  const { words, markSuccess } = useDictionaryStore();
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [dictionaryStats, setDictionaryStats] = useState<DictionaryStats | null>(null);
  const [wordOfWeek, setWordOfWeek] = useState<VocabularyWord | null>(null);
  const [certificate, setCertificate] = useState<CertificateStatus>({ available: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingWord, setSavingWord] = useState(false);
  const [profileForm, setProfileForm] = useState({ name: "", email: "" });
  const [passwordForm, setPasswordForm] = useState({ current: "", next: "", confirm: "" });
  const [settingsMessage, setSettingsMessage] = useState<string | null>(null);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const certificatesRef = useRef<HTMLDivElement | null>(null);
  const settingsRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!user) return;
    setProfileForm({
      name: user.name || user.full_name || (user.email ? user.email.split("@")[0] : ""),
      email: user.email || "",
    });
  }, [user]);

  useEffect(() => {
    if (!user && token && !authLoading) {
      loadUser();
    }
  }, [authLoading, loadUser, token, user]);

  useEffect(() => {
    if (!token) return;
    let active = true;

    const fetchWordOfWeek = async () => {
      try {
        const word = await dictionaryApi.getWordOfWeek?.();
        if (word && active) {
          setWordOfWeek(word);
        }
      } catch (err) {
        console.warn("Failed to fetch word of week:", err);
      }
    };

    fetchWordOfWeek();

    return () => {
      active = false;
    };
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let active = true;

    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!user) {
          await loadUser();
        }
        const [progressPayload, coursesRes] = await Promise.allSettled([
          ProgressService.overview(),
          CourseService.list(),
        ]);
        if (!active) return;

        if (progressPayload.status === "fulfilled") {
          setProgress(progressPayload.value);
        } else {
          console.warn("Failed to load progress", progressPayload.reason);
        }

        if (coursesRes.status === "fulfilled") {
          setCourses(coursesRes.value?.courses || []);
        } else {
          console.warn("Failed to load courses", coursesRes.reason);
        }

        if (progressPayload.status === "rejected" && coursesRes.status === "rejected") {
          const message = extractError(progressPayload.reason, "Не удалось загрузить профиль");
          setError(message);
        }
        const [stats, weeklyWord, certStatus] = await Promise.all([
          dictionaryApi.getStats().catch(() => ({} as DictionaryStats)),
          dictionaryApi.getWordOfWeek().catch(() => null),
          certificatesApi.my().catch(() => ({ available: false } as CertificateStatus)),
        ]);
        if (!active) return;
        setDictionaryStats(stats || {});
        setWordOfWeek(weeklyWord);
        setCertificate(certStatus);
      } catch (err: any) {
        if (!active) return;
        const message = extractError(err, "Не удалось загрузить профиль");
        setError(message);
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchAll();
    return () => {
      active = false;
    };
  }, [token, loadUser, user]);

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

  const displayName = user?.name || user?.full_name || (user?.email ? user.email.split("@")[0] : "—");
  const displayEmail = user?.email || "—";
  const avatarLetter = (displayName || displayEmail || "").charAt(0).toUpperCase() || "Q";
  const streakDays = progress?.streak_days || 0;
  const dailyTarget = progress?.goal_today?.target || user?.daily_minutes || 0;
  const usedMinutes = progress?.goal_today?.completed ? dailyTarget : progress?.xp_today || 0;
  const minutesLeft = Math.max(0, dailyTarget - usedMinutes);
  const courseTitle = progress?.course_title || currentCourse?.name || "—";
  const levelLabel = user?.level || "—";
  const percentValue = progress?.percent || 0;
  const lessonsDone = progress?.completed_lessons || completedLessons.length;
  const lessonsTotal =
    progress?.total_lessons || (currentCourse?.modules || []).reduce((acc, m) => acc + (m.lessons?.length || 0), 0);

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
      const refreshed = await dictionaryApi.getStats();
      setDictionaryStats(refreshed);
    } catch (err: any) {
      const message = err?.response?.data?.detail || "Не удалось обновить словарь";
      setError(message);
    } finally {
      setSavingWord(false);
    }
  };

  const handleProfileSave = async () => {
    setSettingsError(null);
    setSettingsMessage(null);
    try {
      const payload = {
        name: profileForm.name.trim() || undefined,
        email: profileForm.email.trim() || undefined,
      };
      const updated = await usersApi.updateMe(payload);
      setUser(updated as User);
      setSettingsMessage("Профиль обновлен");
    } catch (err: any) {
      setSettingsError(extractError(err, "Не удалось сохранить профиль"));
    }
  };

  const handlePasswordSave = async () => {
    setPasswordError(null);
    setPasswordMessage(null);
    if (!passwordForm.next || !passwordForm.current) {
      setPasswordError("Введите текущий и новый пароли");
      return;
    }
    try {
      const updated = await usersApi.updateMe({
        current_password: passwordForm.current,
        new_password: passwordForm.next,
        confirm_password: passwordForm.confirm,
      });
      setUser(updated as User);
      setPasswordMessage("Пароль изменен");
      setPasswordForm({ current: "", next: "", confirm: "" });
    } catch (err: any) {
      setPasswordError(extractError(err, "Не удалось обновить пароль"));
    }
  };

  const scrollToSection = (ref: { current: HTMLDivElement | null }) => {
    if (ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const handleOpenCertificate = () => {
    if (certificate?.available && certificate.url) {
      window.open(certificate.url, "_blank", "noopener,noreferrer");
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
      <div className="overflow-hidden rounded-2xl bg-gradient-to-r from-slateDeep via-midnight to-slate px-6 py-8 shadow-card">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate/70 text-2xl font-semibold text-gold shadow-soft">
              {avatarLetter}
            </div>
            <div>
              <p className="text-sm uppercase tracking-wide text-gold">Профиль</p>
              <h1 className="text-3xl font-semibold text-white">{displayName}</h1>
              <p className="text-sm text-ink/70">{displayEmail}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => scrollToSection(certificatesRef)}
              className="rounded-xl bg-slate px-4 py-3 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
            >
              Мои сертификаты
            </button>
            <button
              type="button"
              onClick={() => scrollToSection(settingsRef)}
              className="rounded-xl bg-gold px-4 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            >
              Настройки
            </button>
          </div>
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl bg-slate/40 p-4 shadow-inner">
            <p className="text-xs uppercase tracking-wide text-ink/60">Дней подряд</p>
            <p className="text-3xl font-bold text-gold">{formatNumber(streakDays)}</p>
          </div>
          <div className="rounded-xl bg-slate/40 p-4 shadow-inner">
            <p className="text-xs uppercase tracking-wide text-ink/60">Слов выучено</p>
            <p className="text-3xl font-bold text-gold">{formatNumber(learnedWordsCount)}</p>
          </div>
          <div className="rounded-xl bg-slate/40 p-4 shadow-inner">
            <p className="text-xs uppercase tracking-wide text-ink/60">Минут осталось сегодня</p>
            <p className="text-3xl font-bold text-gold">{formatNumber(minutesLeft)}</p>
          </div>
        </div>
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="card-surface space-y-4 p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-gold">Текущий прогресс</p>
              <h2 className="text-2xl font-semibold text-white">{courseTitle}</h2>
              <p className="text-sm text-ink/70">Уровень: {levelLabel}</p>
            </div>
            <span className="rounded-full bg-slate px-4 py-2 text-sm font-semibold text-gold">{percentValue}%</span>
          </div>
          <ProgressBar value={percentValue} />
          <div className="flex flex-wrap gap-3 text-sm text-ink/80">
            <span>Уроки: {lessonsDone} из {lessonsTotal}</span>
            <span>Streak: {formatNumber(streakDays)} дней</span>
            <span>Цель: {dailyTarget} минут/день</span>
          </div>
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
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div ref={certificatesRef} className="card-surface space-y-4 p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-semibold text-gold">Мои сертификаты</p>
              <h3 className="text-xl font-semibold text-white">Подтверждение завершения курса</h3>
              <p className="text-sm text-ink/70">Доступно после прохождения 100% уроков.</p>
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${certificate.available ? "bg-green-600/30 text-green-200" : "bg-slate/70 text-ink/70"}`}>
              {certificate.available ? "Готов" : "Ожидает"}
            </span>
          </div>
          {certificate.available && certificate.url ? (
            <button
              type="button"
              onClick={handleOpenCertificate}
              className="w-full rounded-xl bg-gold px-4 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            >
              Открыть сертификат
            </button>
          ) : (
            <div className="rounded-lg border border-dashed border-slate/50 bg-slate/30 px-4 py-3 text-sm text-ink/70">
              Сертификат появится после прохождения курса. Продолжайте учиться — вы близко!
            </div>
          )}
        </div>

        <div ref={settingsRef} className="card-surface space-y-5 p-6">
          <div>
            <p className="text-sm font-semibold text-gold">Настройки</p>
            <h3 className="text-xl font-semibold text-white">Данные профиля</h3>
            <p className="text-sm text-ink/70">Обновите имя и email, чтобы оставаться на связи.</p>
          </div>
          <div className="space-y-3">
            <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
              Имя
              <input
                type="text"
                value={profileForm.name}
                onChange={(e) => setProfileForm((prev) => ({ ...prev, name: e.target.value }))}
                className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
                placeholder="Как вас называть"
              />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
              Email
              <input
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))}
                className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
                placeholder="you@example.com"
              />
            </label>
            {settingsError && <p className="text-sm text-red-400">{settingsError}</p>}
            {settingsMessage && <p className="text-sm text-green-300">{settingsMessage}</p>}
            <button
              type="button"
              onClick={handleProfileSave}
              className="w-full rounded-xl bg-gold px-4 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            >
              Сохранить данные
            </button>
          </div>

          <div className="mt-4 rounded-xl border border-slate/50 p-4">
            <h4 className="text-base font-semibold text-white">Смена пароля</h4>
            <p className="text-xs text-ink/60">Минимальная валидация, понятные ошибки.</p>
            <div className="mt-3 space-y-3">
              <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
                Текущий пароль
                <input
                  type="password"
                  value={passwordForm.current}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, current: e.target.value }))}
                  className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
                  placeholder="••••••••"
                />
              </label>
              <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
                Новый пароль
                <input
                  type="password"
                  value={passwordForm.next}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, next: e.target.value }))}
                  className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
                  placeholder="Новый пароль"
                />
              </label>
              <label className="flex flex-col gap-2 text-sm font-semibold text-ink">
                Повторите пароль
                <input
                  type="password"
                  value={passwordForm.confirm}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirm: e.target.value }))}
                  className="w-full rounded-xl border border-slate/40 bg-midnight px-3 py-3 text-base text-ink shadow-inner focus:border-gold focus:outline-none"
                  placeholder="Повторите"
                />
              </label>
              {passwordError && <p className="text-sm text-red-400">{passwordError}</p>}
              {passwordMessage && <p className="text-sm text-green-300">{passwordMessage}</p>}
              <button
                type="button"
                onClick={handlePasswordSave}
                className="w-full rounded-xl bg-slate px-4 py-3 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
              >
                Обновить пароль
              </button>
            </div>
          </div>
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
