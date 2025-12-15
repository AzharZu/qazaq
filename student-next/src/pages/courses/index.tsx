import Link from "next/link";
import { useEffect, useState } from "react";
import ProgressBar from "@/components/ProgressBar";
import { coursesApi } from "@/lib/api/courses";
import { Course } from "@/types/course";

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await coursesApi.list();
        setCourses(data);
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Не удалось загрузить курсы");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="rounded-2xl bg-panel p-8 text-ink shadow-card">Загрузка курсов...</div>;
  }

  if (error) {
    return <div className="rounded-2xl bg-panel p-8 text-red-300 shadow-card">{error}</div>;
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-gold">Курсы</p>
        <h1 className="text-4xl font-semibold text-white">Выберите курс</h1>
        <p className="text-sm text-ink/80">Каждый курс включает модули, уроки и практику.</p>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {courses.map((course) => {
          const progressValue = course.progress_percent || 0;
          const inProgress = progressValue > 0 || Boolean(course.next_lesson);
          return (
            <div key={course.id} className="space-y-4 rounded-2xl bg-panel p-6 shadow-card">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-xl font-semibold text-white">{course.name}</h3>
                  <p className="mt-2 text-sm text-ink/80">{course.description}</p>
                </div>
                <span className="rounded-full bg-slate px-3 py-1 text-xs font-semibold text-ink shadow-soft">
                  {progressValue}% 
                </span>
              </div>
              <div className="space-y-2">
                <p className="text-xs font-semibold text-ink/70">Прогресс</p>
                <ProgressBar value={progressValue} />
              </div>
              {course.next_lesson && (
                <div className="rounded-xl bg-slate/60 px-4 py-3 text-sm text-ink shadow-inner">
                  Следующий урок: <span className="font-semibold text-white">{course.next_lesson.title}</span>
                </div>
              )}
              <div className="flex flex-col gap-3">
                <Link
                  href={`/course/${course.id}`}
                  className="w-full rounded-xl bg-gold px-4 py-3 text-center text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
                >
                  Подробнее
                </Link>
                <Link
                  href={course.next_lesson ? `/lesson/${course.next_lesson.id}` : `/course/${course.id}`}
                  className={`w-full rounded-xl px-4 py-3 text-center text-sm font-semibold shadow-soft transition ${
                    inProgress ? "bg-slate text-ink hover:bg-slateDeep hover:text-white" : "bg-slate/70 text-ink"
                  }`}
                >
                  {inProgress ? "Продолжить" : "Начать"}
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
