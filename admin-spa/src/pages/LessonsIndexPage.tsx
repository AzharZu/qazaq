import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { lessonBuilderApi } from "../api/lessonBuilder";
import { Lesson } from "../types";
import { Button } from "../components/ui/button";

export default function LessonsIndexPage() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await lessonBuilderApi.listLessons();
      setLessons(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const grouped = useMemo(() => {
    const groups: Record<string, Lesson[]> = {};
    lessons.forEach((lesson) => {
      const key = String(lesson.module_id || "unassigned");
      if (!groups[key]) groups[key] = [];
      groups[key].push(lesson);
    });
    return groups;
  }, [lessons]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Lesson Builder</p>
          <h1 className="text-2xl font-bold text-slate-900">Lessons</h1>
          <p className="text-sm text-slate-600">Open any lesson to edit blocks, preview, and publish.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          Refresh
        </Button>
      </div>

      {loading ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">Loading lessons…</div>
      ) : (
        <div className="space-y-4">
          {Object.keys(grouped).map((moduleId) => (
            <div key={moduleId} className="space-y-2 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-slate-700">Module {moduleId}</div>
                <div className="text-xs text-slate-500">
                  {grouped[moduleId].length} lesson{grouped[moduleId].length === 1 ? "" : "s"}
                </div>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {grouped[moduleId]
                  .sort((a, b) => (a.order || 0) - (b.order || 0))
                  .map((lesson) => (
                    <div
                      key={lesson.id}
                      className="flex flex-col gap-2 rounded-xl border border-slate-100 bg-gradient-to-br from-white to-slate-50 p-4 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-xs uppercase text-slate-400">#{lesson.id}</div>
                          <div className="text-lg font-semibold text-slate-900">{lesson.title}</div>
                          <div className="text-sm text-slate-600 line-clamp-2">{lesson.description}</div>
                        </div>
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            lesson.status === "published"
                              ? "bg-emerald-50 text-emerald-700"
                              : lesson.status === "archived"
                                ? "bg-slate-100 text-slate-500"
                                : "bg-amber-50 text-amber-700"
                          }`}
                        >
                          {lesson.status || "draft"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span>Order: {lesson.order}</span>
                        <span>Difficulty: {lesson.difficulty || "n/a"}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/admin/lessons/${lesson.id}/builder`}
                          className="flex-1 rounded-lg bg-slate-900 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-slate-800"
                        >
                          Open Builder
                        </Link>
                        <Link
                          to={`/lesson/${lesson.id}?preview=1`}
                          target="_blank"
                          className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                        >
                          Preview
                        </Link>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
