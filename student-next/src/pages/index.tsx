import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import ProgressBar from "@/components/ProgressBar";
import TelegramCta from "@/components/TelegramCta";
import client from "@/lib/api/client";
import { ProgressResponse } from "@/types/progress";

const featureCards = [
  { title: "AutoChecker", text: "Проверка письменных работ с подсветкой ошибок и рекомендациями по улучшению." },
  { title: "Словарь", text: "Интерактивные карточки с повторением, картинками и озвучкой." },
  { title: "Тестирование", text: "Адаптивный тест уровня и квизы в каждом уроке." },
  { title: "Профиль", text: "История обучения, прогресс, streak и сертификаты." },
];

export default function HomePage() {
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(false);

  useEffect(() => {
    const fetchProgress = async () => {
      setLoadingProgress(true);
      try {
        const { data } = await client.get<ProgressResponse>("/progress");
        setProgress(data);
      } catch (err) {
        setProgress(null);
      } finally {
        setLoadingProgress(false);
      }
    };
    fetchProgress();
  }, []);

  const nextLesson = useMemo(() => progress?.next_lesson || null, [progress]);

  return (
    <div className="space-y-14 text-ink">
      <section className="grid gap-10 rounded-2xl bg-panel px-8 py-10 shadow-card md:grid-cols-2">
        <div className="space-y-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-gold">Изучайте казахский уверенно</p>
          <h1 className="text-4xl font-semibold leading-tight text-white md:text-5xl">
            Изучайте казахский язык. Легко и результативно.
          </h1>
          <p className="text-lg text-ink">
            Персонализированные курсы, проверка письменности ИИ, интерактивные карточки и адаптивные тесты — всё в одном месте.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/level-test"
              className="rounded-xl bg-gold px-6 py-3 text-base font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            >
              Начать обучение
            </Link>
            <Link
              href="/courses"
              className="rounded-xl bg-slate px-6 py-3 text-base font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
            >
              Узнать больше
            </Link>
          </div>
        </div>
        <div className="flex items-center justify-center">
          <div className="relative w-full max-w-md min-h-[260px] overflow-hidden rounded-2xl bg-gradient-to-br from-slate via-midnight to-slateDeep shadow-inner md:aspect-[4/3] md:min-h-0">
            <Image
              src="/images/hero-mascot.png"
              alt="Qazaq Mentor иллюстрация"
              fill
              priority
              sizes="(max-width: 768px) 90vw, 420px"
              className="object-contain"
            />
          </div>
        </div>
      </section>

      <TelegramCta />

      <section className="space-y-5">
        <h2 className="text-2xl font-semibold text-white">Продолжайте обучение</h2>
        <div className="rounded-2xl bg-panel p-6 shadow-card">
          {loadingProgress ? (
            <p className="text-sm text-ink/70">Загружаем прогресс...</p>
          ) : progress ? (
            <div className="grid gap-4 md:grid-cols-[1.5fr_1fr]">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gold">Текущий курс</p>
                    <h3 className="text-2xl font-semibold text-white">{progress.course_title || "Ваш курс"}</h3>
                    {nextLesson && <p className="text-sm text-ink/80">Следующий урок: {nextLesson.title}</p>}
                  </div>
                  <span className="rounded-full bg-slate px-4 py-2 text-xs font-semibold text-ink shadow-soft">
                    {progress.percent}% прогресса
                  </span>
                </div>
                <ProgressBar value={progress.percent} />
                <div className="flex flex-wrap gap-3 text-xs font-semibold text-ink/70">
                  <span>Уроки: {progress.completed_lessons}/{progress.total_lessons}</span>
                  <span>Streak: {progress.streak_days} дней</span>
                  <span>Опыт: {progress.xp_total} XP</span>
                </div>
                {nextLesson && (
                  <Link
                    href={`/lesson/${nextLesson.id}`}
                    className="inline-flex w-fit rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
                  >
                    Продолжить
                  </Link>
                )}
              </div>
              <div className="rounded-xl bg-slate/60 p-5 shadow-inner">
                <p className="text-sm font-semibold text-ink/80">Цель сегодня</p>
                <p className="text-3xl font-bold text-white">
                  {progress.goal_today?.target || 0}
                  <span className="text-base font-semibold text-ink/60"> минут</span>
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  {progress.goal_today?.completed ? "Цель выполнена" : "Ещё чуть-чуть — и цель будет достигнута"}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-gold">Не начали курс</p>
                <p className="text-lg text-ink/80">Пройдите тест уровня — подберём программу под вас.</p>
              </div>
              <Link href="/level-test" className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark">
                Пройти тест
              </Link>
            </div>
          )}
        </div>
      </section>

      <section className="space-y-5">
        <h2 className="text-2xl font-semibold text-white">Возможности платформы</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {featureCards.map((card) => (
            <div key={card.title} className="rounded-2xl bg-panel p-6 shadow-card">
              <p className="text-sm font-semibold text-gold">✓ {card.title}</p>
              <p className="mt-2 text-sm text-ink/80">{card.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl bg-panel px-8 py-10 text-center shadow-card">
        <h3 className="text-3xl font-semibold text-white">Готовы начать?</h3>
        <p className="mt-3 text-ink/80">Тысячи учащихся уже улучшили свой казахский. Присоединяйтесь.</p>
        <div className="mt-5 flex justify-center gap-3">
          <Link
            href="/courses"
            className="rounded-xl bg-gold px-6 py-3 text-base font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
          >
            Перейти к курсам
          </Link>
          <Link
            href="/level-test"
            className="rounded-xl border border-slate px-6 py-3 text-base font-semibold text-ink transition hover:bg-slate/60 hover:text-white"
          >
            Определить уровень
          </Link>
        </div>
      </section>
    </div>
  );
}
