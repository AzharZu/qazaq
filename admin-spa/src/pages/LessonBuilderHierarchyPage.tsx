import { useState, useEffect, useCallback } from "react";
import { adminCoursesApi, adminModulesApi, adminLessonsApi } from "../api/entities";
import { Course, Module, Lesson } from "../types";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Modal } from "../components/ui/modal";
import { ConfirmModal } from "../components/ui/confirm-modal";
import { useToast } from "../components/ui/use-toast";
import { VideoPlayer } from "../components/ui/video-player";

export default function LessonBuilderHierarchyPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [lessons, setLessons] = useState<Record<number, Lesson[]>>({});
  const [expandedModules, setExpandedModules] = useState<Set<number>>(new Set());
  
  const [courseModal, setCourseModal] = useState<{ open: boolean; editing?: Course }>({ open: false });
  const [moduleModal, setModuleModal] = useState<{ open: boolean; editing?: Module }>({ open: false });
  const [lessonModal, setLessonModal] = useState<{ open: boolean; moduleId?: number; editing?: Lesson }>({ open: false });
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: "course" | "module" | "lesson"; id: number } | null>(null);
  
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Load courses
  const loadCourses = useCallback(async () => {
    try {
      const data = await adminCoursesApi.list();
      setCourses(data);
      if (data.length > 0) {
        setSelectedCourseId(prev => prev || data[0].id);
      }
    } catch (err: any) {
      toast({ title: "Failed to load courses", description: err?.message, variant: "destructive" });
    }
  }, [toast]);

  // Load modules for selected course
  const loadModules = useCallback(async () => {
    if (!selectedCourseId) {
      setModules([]);
      return;
    }
    try {
      const data = await adminModulesApi.list(selectedCourseId);
      setModules(data.sort((a, b) => a.order - b.order));
      // Auto-expand first module
      if (data.length > 0) {
        setExpandedModules(new Set([data[0].id]));
      }
    } catch (err: any) {
      toast({ title: "Failed to load modules", description: err?.message, variant: "destructive" });
    }
  }, [selectedCourseId, toast]);

  // Load lessons for a module
  const loadLessons = useCallback(async (moduleId: number) => {
    try {
      const data = await adminLessonsApi.list(moduleId);
      setLessons(prev => ({ ...prev, [moduleId]: data.sort((a, b) => a.order - b.order) }));
    } catch (err: any) {
      toast({ title: "Failed to load lessons", description: err?.message, variant: "destructive" });
    }
  }, [toast]);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  useEffect(() => {
    loadModules();
  }, [loadModules]);

  // Load lessons when modules are expanded
  useEffect(() => {
    expandedModules.forEach(moduleId => {
      if (!lessons[moduleId]) {
        loadLessons(moduleId);
      }
    });
  }, [expandedModules, lessons, loadLessons]);

  const toggleModule = (moduleId: number) => {
    setExpandedModules(prev => {
      const next = new Set(prev);
      if (next.has(moduleId)) {
        next.delete(moduleId);
      } else {
        next.add(moduleId);
      }
      return next;
    });
  };

  const openCourseCreate = () => {
    setFormData({});
    setCourseModal({ open: true });
  };

  const openCourseEdit = (course: Course) => {
    setFormData(course);
    setCourseModal({ open: true, editing: course });
  };

  const saveCourse = async () => {
    setLoading(true);
    try {
      if (courseModal.editing) {
        await adminCoursesApi.update(courseModal.editing.id, formData);
        toast({ title: "Course updated" });
      } else {
        await adminCoursesApi.create(formData);
        toast({ title: "Course created" });
      }
      setCourseModal({ open: false });
      loadCourses();
    } catch (err: any) {
      toast({ title: "Save failed", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const openModuleCreate = () => {
    if (!selectedCourseId) {
      toast({ title: "Please select a course first", variant: "destructive" });
      return;
    }
    setFormData({ course_id: selectedCourseId, order: modules.length + 1 });
    setModuleModal({ open: true });
  };

  const openModuleEdit = (module: Module) => {
    setFormData(module);
    setModuleModal({ open: true, editing: module });
  };

  const saveModule = async () => {
    if (!formData.course_id) {
      toast({ title: "Course is required", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      if (moduleModal.editing) {
        await adminModulesApi.update(moduleModal.editing.id, formData);
        toast({ title: "Module updated" });
      } else {
        await adminModulesApi.create(formData);
        toast({ title: "Module created" });
      }
      setModuleModal({ open: false });
      loadModules();
    } catch (err: any) {
      toast({ title: "Save failed", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const openLessonCreate = (moduleId: number) => {
    const moduleLessons = lessons[moduleId] || [];
    setFormData({
      module_id: moduleId,
      title: "",
      status: "draft",
      language: "kk",
      order: moduleLessons.length + 1,
    });
    setLessonModal({ open: true, moduleId });
  };

  const openLessonEdit = (lesson: Lesson) => {
    setFormData(lesson);
    setLessonModal({ open: true, moduleId: lesson.module_id, editing: lesson });
  };

  const saveLesson = async () => {
    if (!formData.module_id) {
      toast({ title: "Module is required", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      if (lessonModal.editing) {
        await adminLessonsApi.update(lessonModal.editing.id, formData);
        toast({ title: "Lesson updated" });
      } else {
        await adminLessonsApi.create(formData);
        toast({ title: "Lesson created" });
      }
      setLessonModal({ open: false });
      if (formData.module_id) {
        loadLessons(formData.module_id);
      }
    } catch (err: any) {
      toast({ title: "Save failed", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setLoading(true);
    try {
      if (deleteConfirm.type === "course") {
        await adminCoursesApi.remove(deleteConfirm.id);
        if (selectedCourseId === deleteConfirm.id) {
          setSelectedCourseId(null);
        }
        toast({ title: "Course deleted" });
      } else if (deleteConfirm.type === "module") {
        await adminModulesApi.remove(deleteConfirm.id);
        toast({ title: "Module deleted (lessons were also deleted)" });
      } else if (deleteConfirm.type === "lesson") {
        await adminLessonsApi.remove(deleteConfirm.id);
        toast({ title: "Lesson deleted" });
      }
      setDeleteConfirm(null);
      loadCourses();
      loadModules();
    } catch (err: any) {
      toast({ title: "Delete failed", description: err?.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Lesson Builder</h1>
          <p className="text-gray-600 mt-1">Manage courses, modules, and lessons</p>
        </div>
        <Button onClick={openCourseCreate}>+ Create Course</Button>
      </div>

      {/* Course Selector */}
      <div className="bg-white rounded-lg border p-4">
        <label className="block text-sm font-medium mb-2">Select Course</label>
        <div className="flex gap-2">
          <select
            className="flex-1 px-3 py-2 border rounded-md"
            value={selectedCourseId || ""}
            onChange={(e) => setSelectedCourseId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">-- Select a course --</option>
            {courses.map(course => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))}
          </select>
          {selectedCourseId && (
            <>
              <Button variant="ghost" onClick={() => {
                const course = courses.find(c => c.id === selectedCourseId);
                if (course) openCourseEdit(course);
              }}>
                Edit
              </Button>
              <Button variant="ghost" onClick={() => setDeleteConfirm({ type: "course", id: selectedCourseId })}>
                Delete
              </Button>
            </>
          )}
        </div>
      </div>

      {selectedCourseId && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Modules</h2>
            <Button onClick={openModuleCreate}>+ Add Module</Button>
          </div>

          {modules.length === 0 ? (
            <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
              No modules yet. Create your first module!
            </div>
          ) : (
            <div className="space-y-2">
              {modules.map(module => (
                <div key={module.id} className="bg-white border rounded-lg">
                  <div className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3 flex-1">
                      <button
                        onClick={() => toggleModule(module.id)}
                        className="text-gray-600 hover:text-gray-900"
                      >
                        {expandedModules.has(module.id) ? "▼" : "▶"}
                      </button>
                      <div className="flex-1">
                        <div className="font-medium">{module.name}</div>
                        {module.description && (
                          <div className="text-sm text-gray-500">{module.description}</div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => openModuleEdit(module)}>
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteConfirm({ type: "module", id: module.id })}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>

                  {expandedModules.has(module.id) && (
                    <div className="border-t bg-gray-50 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-medium">Lessons</h3>
                        <Button size="sm" onClick={() => openLessonCreate(module.id)}>
                          + Add Lesson
                        </Button>
                      </div>

                      {lessons[module.id]?.length === 0 ? (
                        <div className="text-sm text-gray-500 py-4 text-center">
                          No lessons yet. Create your first lesson!
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {(lessons[module.id] || []).map(lesson => (
                            <div
                              key={lesson.id}
                              className="bg-white border rounded p-3 flex items-center justify-between"
                            >
                              <div className="flex-1">
                                <div className="font-medium">{lesson.title}</div>
                                {lesson.description && (
                                  <div className="text-sm text-gray-500 mt-1">{lesson.description}</div>
                                )}
                                {lesson.video_url && (
                                  <div className="mt-2">
                                    <VideoPlayer
                                      videoType={lesson.video_type || "youtube"}
                                      videoUrl={lesson.video_url}
                                    />
                                  </div>
                                )}
                                <div className="text-xs text-gray-400 mt-1">
                                  Status: {lesson.status} | Order: {lesson.order}
                                </div>
                              </div>
                              <div className="flex gap-2 ml-4">
                                <Button variant="ghost" size="sm" onClick={() => openLessonEdit(lesson)}>
                                  Edit
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setDeleteConfirm({ type: "lesson", id: lesson.id })}
                                >
                                  Delete
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Course Modal */}
      <Modal
        title={courseModal.editing ? "Edit Course" : "Create Course"}
        open={courseModal.open}
        onOpenChange={(open) => setCourseModal({ open })}
        widthClass="w-[600px]"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <Input
              value={formData.name || ""}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Slug</label>
            <Input
              value={formData.slug || ""}
              onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              disabled={!!courseModal.editing}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Audience</label>
            <Input
              value={formData.audience || ""}
              onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCourseModal({ open: false })}>
              Cancel
            </Button>
            <Button onClick={saveCourse} disabled={loading}>
              {courseModal.editing ? "Save" : "Create"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Module Modal */}
      <Modal
        title={moduleModal.editing ? "Edit Module" : "Create Module"}
        open={moduleModal.open}
        onOpenChange={(open) => setModuleModal({ open })}
        widthClass="w-[600px]"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name *</label>
            <Input
              value={formData.name || ""}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Order</label>
            <Input
              type="number"
              value={formData.order || ""}
              onChange={(e) => setFormData({ ...formData, order: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setModuleModal({ open: false })}>
              Cancel
            </Button>
            <Button onClick={saveModule} disabled={loading}>
              {moduleModal.editing ? "Save" : "Create"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Lesson Modal */}
      <Modal
        title={lessonModal.editing ? "Edit Lesson" : "Create Lesson"}
        open={lessonModal.open}
        onOpenChange={(open) => setLessonModal({ open })}
        widthClass="w-[700px]"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Title *</label>
            <Input
              value={formData.title || ""}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                className="w-full px-3 py-2 border rounded-md"
                value={formData.status || "draft"}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Order</label>
              <Input
                type="number"
                value={formData.order || ""}
                onChange={(e) => setFormData({ ...formData, order: Number(e.target.value) })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Video Type</label>
              <select
                className="w-full px-3 py-2 border rounded-md"
                value={formData.video_type || ""}
                onChange={(e) => setFormData({ ...formData, video_type: e.target.value || null })}
              >
                <option value="">None</option>
                <option value="youtube">YouTube</option>
                <option value="vimeo">Vimeo</option>
                <option value="file">Self-hosted (MP4)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Video URL</label>
              <Input
                value={formData.video_url || ""}
                onChange={(e) => setFormData({ ...formData, video_url: e.target.value || null })}
                placeholder="YouTube/Vimeo URL or MP4 file URL"
              />
            </div>
          </div>
          {formData.video_url && formData.video_type && (
            <div>
              <label className="block text-sm font-medium mb-1">Preview</label>
              <VideoPlayer
                videoType={formData.video_type}
                videoUrl={formData.video_url}
              />
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setLessonModal({ open: false })}>
              Cancel
            </Button>
            <Button onClick={saveLesson} disabled={loading}>
              {lessonModal.editing ? "Save" : "Create"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmModal
        open={!!deleteConfirm}
        title="Confirm Delete"
        message={
          deleteConfirm?.type === "course"
            ? "Are you sure you want to delete this course? All modules and lessons will be deleted."
            : deleteConfirm?.type === "module"
              ? "Are you sure you want to delete this module? All lessons will be deleted."
              : "Are you sure you want to delete this lesson?"
        }
        onConfirm={handleDelete}
        onCancel={() => setDeleteConfirm(null)}
      />
    </div>
  );
}
