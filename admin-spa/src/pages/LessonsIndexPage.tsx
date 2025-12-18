import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { lessonBuilderApi } from "../api/lessonBuilder";
import { Course, Lesson, Module } from "../types";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { ConfirmModal } from "../components/ui/confirm-modal";
import { useToast } from "../components/ui/use-toast";
import { Spinner } from "../components/ui/spinner";

type ConfirmState = { open: boolean; type?: "module" | "lesson"; id?: number; moduleId?: number };
type ModuleWithLessons = Module & { lessons: Lesson[] };

export default function LessonsIndexPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [modules, setModules] = useState<ModuleWithLessons[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [loadingModules, setLoadingModules] = useState(false);
  const [newCourse, setNewCourse] = useState({ name: "", slug: "", description: "", audience: "" });
  const [newModule, setNewModule] = useState({ name: "", description: "" });
  const [newLessonTitles, setNewLessonTitles] = useState<Record<number, string>>({});
  const [editingModuleId, setEditingModuleId] = useState<number | null>(null);
  const [moduleDraft, setModuleDraft] = useState<Partial<Module>>({});
  const [lessonDrafts, setLessonDrafts] = useState<Record<number, Partial<Lesson>>>({});
  const [confirm, setConfirm] = useState<ConfirmState>({ open: false });
  const { toast } = useToast();

  const selectedCourse = useMemo(
    () => courses.find((c) => c.id === selectedCourseId) || null,
    [courses, selectedCourseId],
  );

  const loadCourses = async () => {
    setLoadingCourses(true);
    try {
      const data = await lessonBuilderApi.listCourses();
      setCourses(data);
      if (data.length) {
        if (!selectedCourseId) {
          setSelectedCourseId(data[0].id);
        } else if (!data.some((c) => c.id === selectedCourseId)) {
          setSelectedCourseId(data[0].id);
        }
      } else {
        setSelectedCourseId(null);
      }
    } catch (err: any) {
      toast({ title: "Не удалось загрузить курсы", description: err?.message || "Ошибка", variant: "destructive" });
    } finally {
      setLoadingCourses(false);
    }
  };

  const loadModules = async (courseId: number | null) => {
    if (!courseId) {
      setModules([]);
      return;
    }
    setLoadingModules(true);
    try {
      const data = await lessonBuilderApi.listModules(courseId);
      const normalized: ModuleWithLessons[] = (data || []).map((mod) => ({
        ...mod,
        lessons: [...(mod.lessons || [])].sort((a, b) => (a.order || 0) - (b.order || 0)),
      }));
      normalized.sort((a, b) => (a.order || 0) - (b.order || 0));
      setModules(normalized);
    } catch (err: any) {
      toast({ title: "Не удалось загрузить модули", description: err?.message || "Ошибка", variant: "destructive" });
    } finally {
      setLoadingModules(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, []);

  useEffect(() => {
    loadModules(selectedCourseId);
  }, [selectedCourseId]);

  const handleCreateCourse = async () => {
    if (!newCourse.name.trim() || !newCourse.slug.trim() || !newCourse.description.trim() || !newCourse.audience.trim()) {
      toast({ title: "Заполните название, slug, описание и аудиторию", variant: "destructive" });
      return;
    }
    try {
      const created = await lessonBuilderApi.createCourse(newCourse);
      setCourses((prev) => [...prev, created]);
      setSelectedCourseId(created.id);
      setNewCourse({ name: "", slug: "", description: "", audience: "" });
      toast({ title: "Курс создан" });
    } catch (err: any) {
      toast({ title: "Не удалось создать курс", description: err?.message || "Ошибка", variant: "destructive" });
    }
  };

  const handleCreateModule = async () => {
    if (!selectedCourseId) {
      toast({ title: "Сначала выберите курс", variant: "destructive" });
      return;
    }
    if (!newModule.name.trim()) {
      toast({ title: "Название модуля обязательно", variant: "destructive" });
      return;
    }
    try {
      const created = await lessonBuilderApi.createModule({
        ...newModule,
        course_id: selectedCourseId,
      });
      setModules((prev) => [...prev, { ...created, lessons: [] }].sort((a, b) => (a.order || 0) - (b.order || 0)));
      setNewModule({ name: "", description: "" });
      toast({ title: "Модуль создан" });
    } catch (err: any) {
      toast({ title: "Не удалось создать модуль", description: err?.message || "Ошибка", variant: "destructive" });
    }
  };

  const startEditModule = (module: ModuleWithLessons) => {
    setEditingModuleId(module.id);
    setModuleDraft({ name: module.name, description: module.description, order: module.order });
  };

  const saveModule = async () => {
    if (!editingModuleId) return;
    try {
      const updated = await lessonBuilderApi.updateModule(editingModuleId, moduleDraft);
      setModules((prev) =>
        prev
          .map((m) => (m.id === editingModuleId ? { ...m, ...updated, lessons: updated.lessons || m.lessons || [] } : m))
          .sort((a, b) => (a.order || 0) - (b.order || 0)),
      );
      setEditingModuleId(null);
      setModuleDraft({});
      toast({ title: "Модуль обновлен" });
    } catch (err: any) {
      toast({ title: "Не удалось обновить модуль", description: err?.message || "Ошибка", variant: "destructive" });
    }
  };

  const handleCreateLesson = async (moduleId: number) => {
    const title = (newLessonTitles[moduleId] || "").trim();
    if (!title) {
      toast({ title: "Название урока обязательно", variant: "destructive" });
      return;
    }
    try {
      const created = await lessonBuilderApi.createLesson({
        module_id: moduleId,
        title,
      });
      setModules((prev) =>
        prev.map((m) =>
          m.id === moduleId
            ? {
                ...m,
                lessons: [...(m.lessons || []), created].sort((a, b) => (a.order || 0) - (b.order || 0)),
              }
            : m,
        ),
      );
      setNewLessonTitles((prev) => ({ ...prev, [moduleId]: "" }));
      toast({ title: "Урок создан" });
    } catch (err: any) {
      toast({ title: "Не удалось создать урок", description: err?.message || "Ошибка", variant: "destructive" });
    }
  };

  const startLessonEdit = (lesson: Lesson) => {
    setLessonDrafts((prev) => ({
      ...prev,
      [lesson.id]: { title: lesson.title, order: lesson.order, description: lesson.description },
    }));
  };

  const cancelLessonEdit = (lessonId: number) => {
    setLessonDrafts((prev) => {
      const next = { ...prev };
      delete next[lessonId];
      return next;
    });
  };

  const saveLesson = async (lessonId: number, moduleId: number) => {
    const draft = lessonDrafts[lessonId];
    if (!draft) return;
    try {
      const updated = await lessonBuilderApi.updateLesson(lessonId, draft);
      setModules((prev) =>
        prev.map((m) =>
          m.id === moduleId
            ? {
                ...m,
                lessons: (m.lessons || [])
                  .map((l) => (l.id === lessonId ? { ...l, ...updated } : l))
                  .sort((a, b) => (a.order || 0) - (b.order || 0)),
              }
            : m,
        ),
      );
      cancelLessonEdit(lessonId);
      toast({ title: "Урок обновлен" });
    } catch (err: any) {
      toast({ title: "Не удалось обновить урок", description: err?.message || "Ошибка", variant: "destructive" });
    }
  };

  const handleDeleteConfirmed = async () => {
    if (!confirm.open || !confirm.id) return;
    try {
      if (confirm.type === "module") {
        await lessonBuilderApi.deleteModule(confirm.id);
        setModules((prev) => prev.filter((m) => m.id !== confirm.id));
        toast({ title: "Модуль удален вместе с уроками" });
      } else if (confirm.type === "lesson" && confirm.moduleId) {
        await lessonBuilderApi.deleteLesson(confirm.id);
        setModules((prev) =>
          prev.map((m) =>
            m.id === confirm.moduleId ? { ...m, lessons: (m.lessons || []).filter((l) => l.id !== confirm.id) } : m,
          ),
        );
        toast({ title: "Урок удален" });
      }
    } catch (err: any) {
      toast({ title: "Удаление не удалось", description: err?.message || "Ошибка", variant: "destructive" });
    } finally {
      setConfirm({ open: false });
    }
  };

  const selectedModules = useMemo(
    () => modules.map((m) => ({ ...m, lessons: [...(m.lessons || [])].sort((a, b) => (a.order || 0) - (b.order || 0)) })),
    [modules],
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Lesson Builder</p>
          <h1 className="text-2xl font-bold text-slate-900">Course → Module → Lesson</h1>
          <p className="text-sm text-slate-600">Создавайте модули только внутри курса, а уроки — только внутри модуля.</p>
        </div>
        <Button variant="outline" onClick={() => loadModules(selectedCourseId)} disabled={loadingModules}>
          {loadingModules ? "Loading…" : "Refresh"}
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Курсы</CardTitle>
            <CardDescription>Сначала выберите курс, потом управляйте модулями и уроками.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <label className="text-sm font-medium text-slate-700">Выбранный курс</label>
            <div className="flex items-center gap-2">
              <select
                className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm"
                value={selectedCourseId ?? ""}
                onChange={(e) => setSelectedCourseId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">— выберите курс —</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>
              {loadingCourses ? <Spinner /> : null}
            </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="mb-2 text-sm font-semibold text-slate-800">Создать курс</div>
                <Input
                  placeholder="Название"
                  value={newCourse.name}
                  onChange={(e) => setNewCourse((prev) => ({ ...prev, name: e.target.value }))}
                />
                <Textarea
                  className="mt-2"
                  rows={2}
                  placeholder="Описание"
                  value={newCourse.description}
                  onChange={(e) => setNewCourse((prev) => ({ ...prev, description: e.target.value }))}
                />
                <div className="mt-2 flex items-center gap-2">
                  <Input
                    placeholder="Slug"
                    value={newCourse.slug}
                    onChange={(e) => setNewCourse((prev) => ({ ...prev, slug: e.target.value }))}
                  />
                  <Input
                    placeholder="Аудитория (kids/adult/gov)"
                    value={newCourse.audience}
                    onChange={(e) => setNewCourse((prev) => ({ ...prev, audience: e.target.value }))}
                  />
                  <Button onClick={handleCreateCourse}>Создать</Button>
                </div>
              </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Модули и уроки</CardTitle>
              <CardDescription>Каскад: удаление модуля удаляет его уроки.</CardDescription>
            </div>
            <div className="text-sm text-slate-500">
              {selectedModules.length} модул{selectedModules.length === 1 ? "ь" : "ей"}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedCourse ? (
              <>
                <div className="rounded-lg border border-slate-200 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <div className="text-sm font-semibold text-slate-800">➕ Новый модуль</div>
                    <span className="text-xs text-slate-500">для курса “{selectedCourse.name}”</span>
                  </div>
                  <div className="grid gap-2 md:grid-cols-[2fr_1fr]">
                    <Input
                      placeholder="Название модуля"
                      value={newModule.name}
                      onChange={(e) => setNewModule((prev) => ({ ...prev, name: e.target.value }))}
                    />
                    <Input
                      placeholder="Описание (опционально)"
                      value={newModule.description}
                      onChange={(e) => setNewModule((prev) => ({ ...prev, description: e.target.value }))}
                    />
                  </div>
                  <div className="mt-2 flex justify-end">
                    <Button onClick={handleCreateModule}>Создать модуль</Button>
                  </div>
                </div>

                {loadingModules ? (
                  <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600">
                    <Spinner /> Загружаем модули…
                  </div>
                ) : selectedModules.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
                    Нет модулей. Создайте первый модуль для курса.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {selectedModules.map((module) => {
                      const isEditing = editingModuleId === module.id;
                      return (
                        <div key={module.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="space-y-1">
                              <div className="text-xs uppercase text-slate-400">#{module.id}</div>
                              {isEditing ? (
                                <>
                                  <Input
                                    value={moduleDraft.name || ""}
                                    onChange={(e) => setModuleDraft((prev) => ({ ...prev, name: e.target.value }))}
                                  />
                                  <Textarea
                                    rows={2}
                                    placeholder="Описание"
                                    value={moduleDraft.description || ""}
                                    onChange={(e) => setModuleDraft((prev) => ({ ...prev, description: e.target.value }))}
                                  />
                                  <Input
                                    type="number"
                                    value={moduleDraft.order ?? module.order}
                                    onChange={(e) => setModuleDraft((prev) => ({ ...prev, order: Number(e.target.value) }))}
                                  />
                                </>
                              ) : (
                                <>
                                  <div className="text-lg font-semibold text-slate-900">{module.name}</div>
                                  <div className="text-sm text-slate-600">{module.description || "Без описания"}</div>
                                  <div className="text-xs text-slate-500">Порядок: {module.order}</div>
                                </>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {isEditing ? (
                                <>
                                  <Button variant="outline" size="sm" onClick={() => { setEditingModuleId(null); setModuleDraft({}); }}>
                                    Cancel
                                  </Button>
                                  <Button size="sm" onClick={saveModule}>
                                    Save
                                  </Button>
                                </>
                              ) : (
                                <>
                                  <Button variant="outline" size="sm" onClick={() => startEditModule(module)}>
                                    Edit
                                  </Button>
                                  <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={() => setConfirm({ open: true, type: "module", id: module.id })}
                                  >
                                    Delete
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>

                          <div className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-3">
                            <div className="mb-2 flex items-center justify-between">
                              <div className="text-sm font-semibold text-slate-800">Уроки модуля</div>
                              <div className="text-xs text-slate-500">{module.lessons.length} шт.</div>
                            </div>
                            <div className="grid gap-3">
                              {module.lessons.map((lesson) => {
                                const draft = lessonDrafts[lesson.id];
                                const isLessonEditing = Boolean(draft);
                                return (
                                  <div
                                    key={lesson.id}
                                    className="flex flex-col gap-2 rounded-lg border border-white bg-white p-3 shadow-inner md:flex-row md:items-center md:justify-between"
                                  >
                                    <div className="flex-1 space-y-1">
                                      <div className="flex items-center gap-2">
                                        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                                          #{lesson.id}
                                        </span>
                                        <span className="text-xs text-slate-500">order {lesson.order}</span>
                                        <span
                                          className={`rounded-full px-2 py-1 text-xs font-semibold ${
                                            lesson.status === "published"
                                              ? "bg-emerald-50 text-emerald-700"
                                              : "bg-amber-50 text-amber-700"
                                          }`}
                                        >
                                          {lesson.status || "draft"}
                                        </span>
                                      </div>
                                      {isLessonEditing ? (
                                        <div className="flex flex-col gap-2 md:flex-row md:items-center">
                                          <Input
                                            className="flex-1"
                                            value={draft.title || ""}
                                            onChange={(e) =>
                                              setLessonDrafts((prev) => ({
                                                ...prev,
                                                [lesson.id]: { ...draft, title: e.target.value },
                                              }))
                                            }
                                          />
                                          <Input
                                            type="number"
                                            className="w-24"
                                            value={draft.order ?? lesson.order}
                                            onChange={(e) =>
                                              setLessonDrafts((prev) => ({
                                                ...prev,
                                                [lesson.id]: { ...draft, order: Number(e.target.value) },
                                              }))
                                            }
                                          />
                                        </div>
                                      ) : (
                                        <>
                                          <div className="text-base font-semibold text-slate-900">{lesson.title}</div>
                                          <div className="text-sm text-slate-600 line-clamp-2">{lesson.description || "Без описания"}</div>
                                        </>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-2">
                                      {isLessonEditing ? (
                                        <>
                                          <Button variant="outline" size="sm" onClick={() => cancelLessonEdit(lesson.id)}>
                                            Cancel
                                          </Button>
                                          <Button size="sm" onClick={() => saveLesson(lesson.id, module.id)}>
                                            Save
                                          </Button>
                                        </>
                                      ) : (
                                        <>
                                          <Link
                                            to={`/admin/lessons/${lesson.id}/builder`}
                                            className="rounded-md bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800"
                                          >
                                            Open builder
                                          </Link>
                                          <Button variant="outline" size="sm" onClick={() => startLessonEdit(lesson)}>
                                            Edit
                                          </Button>
                                          <Button
                                            variant="destructive"
                                            size="sm"
                                            onClick={() => setConfirm({ open: true, type: "lesson", id: lesson.id, moduleId: module.id })}
                                          >
                                            Delete
                                          </Button>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                            <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-center">
                              <Input
                                className="flex-1"
                                placeholder="Название урока"
                                value={newLessonTitles[module.id] || ""}
                                onChange={(e) => setNewLessonTitles((prev) => ({ ...prev, [module.id]: e.target.value }))}
                              />
                              <Button size="sm" onClick={() => handleCreateLesson(module.id)}>
                                + Add lesson
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            ) : (
              <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
                Выберите курс, чтобы увидеть связанные модули и уроки.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <ConfirmModal
        open={confirm.open}
        title="Confirm delete"
        message={
          confirm.type === "module"
            ? "Удалить модуль? Его уроки удалятся каскадно."
            : "Удалить урок без возможности восстановления?"
        }
        onConfirm={handleDeleteConfirmed}
        onCancel={() => setConfirm({ open: false })}
      />
    </div>
  );
}
