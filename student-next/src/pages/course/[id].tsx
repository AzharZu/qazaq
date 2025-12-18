import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import ProgressBar from "@/components/ProgressBar";
import { coursesApi } from "@/lib/api/courses";
import { Course } from "@/types/course";
import { LessonSummary } from "@/types/lesson";
import { Module } from "@/types/module";

const getModuleProgress = (module: Module, course?: Course) => {
  const lessons = module.lessons || [];
  const map = course?.progress_map || {};
  const done = lessons.filter((l) => ["done", "finished"].includes(map[l.id] || "")).length;
  const percent = lessons.length ? Math.round((done / lessons.length) * 100) : 0;
  return { done, total: lessons.length, percent };
};

export default function CourseDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const data = await coursesApi.get(id as string);
        setCourse(data);
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Не удалось загрузить курс");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const modules = useMemo(() => course?.modules || [], [course]);

  if (loading) {
    return <div className="rounded-2xl bg-panel p-8 text-ink shadow-card">Загрузка курса...</div>;
  }

  if (error || !course) {
    return <div className="rounded-2xl bg-panel p-8 text-red-300 shadow-card">{error || "Курс не найден"}</div>;
  }
  return (
    <div className="space-y-8">
      <Link href="/courses" className="inline-flex items-center gap-2 text-sm font-semibold text-gold hover:text-white">
        ← Назад
      </Link>

      <div className="rounded-2xl bg-panel p-8 shadow-card">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-gold">Курс</p>
            <h1 className="text-3xl font-semibold text-white">{course.name}</h1>
            <p className="mt-2 text-sm text-ink/80">{course.description}</p>
            {course.next_lesson && (
              <p className="mt-2 text-sm font-semibold text-ink">Последний урок: {course.next_lesson.title}</p>
            )}
          </div>
          <div className="space-y-2 text-right">
            <span className="rounded-full bg-slate px-4 py-2 text-xs font-semibold text-ink shadow-soft">
              {course.progress_percent ?? 0}% готово
            </span>
          </div>
        </div>
        <div className="mt-4">
          <ProgressBar value={course.progress_percent || 0} label="Прогресс по курсу" />
        </div>
        {course.next_lesson && (
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href={`/lesson/${course.next_lesson.id}`}
              className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            >
              Продолжить урок
            </Link>
          </div>
        )}
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold text-white">Модули курса</h2>
        <div className="space-y-4">
          {modules.map((module) => {
            const { percent, done, total } = getModuleProgress(module, course);
            return (
              <div key={module.id} className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-gold">Модуль {module.order}</p>
                    <h3 className="text-xl font-semibold text-white">{module.name}</h3>
                    {module.description && <p className="mt-2 text-sm text-ink/80">{module.description}</p>}
                  </div>
                  <span className="text-lg font-semibold text-gold">{percent}%</span>
                </div>
                <ProgressBar value={percent} />
                <div className="space-y-2">
                  {(module.lessons || []).map((lesson: LessonSummary) => {
                    const status = (course.progress_map || {})[lesson.id];
                    const isDone = status === "done" || status === "finished";
                    return (
                      <div key={lesson.id} className="flex items-center justify-between gap-3 rounded-xl bg-slate/40 px-4 py-3 text-ink shadow-inner">
                        <div>
                          <p className="text-sm font-semibold text-white">{lesson.title}</p>
                          {lesson.description && <p className="text-xs text-ink/70">{lesson.description}</p>}
                        </div>
                        <div className="flex items-center gap-3">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              isDone ? "bg-gold text-slateDeep" : "bg-slate text-ink"
                            }`}
                          >
                            {isDone ? "Пройдено" : "В процессе"}
                          </span>
                          <Link
                            href={`/lesson/${lesson.id}`}
                            className="rounded-xl bg-slate px-3 py-2 text-xs font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
                          >
                            Открыть
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                  {!module.lessons?.length && <p className="text-sm text-ink/70">Уроки скоро появятся</p>}
                </div>
                <div className="text-xs text-ink/60">
                  {done}/{total} уроков пройдено
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
