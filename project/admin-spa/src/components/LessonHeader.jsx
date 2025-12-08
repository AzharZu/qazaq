export default function LessonHeader({
  lesson,
  saving,
  dirty,
  onChange,
  onSave,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
}) {
  return (
    <header className="lesson-header">
      <div className="lesson-header__title">
        <input
          className="title-input"
          value={lesson.title || ""}
          onChange={(e) => onChange({ title: e.target.value })}
          placeholder="Lesson title"
        />
        <div className="meta-row">
          <select value={lesson.status || "draft"} onChange={(e) => onChange({ status: e.target.value })}>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
          <input
            className="chip-input"
            value={lesson.language || "kk"}
            onChange={(e) => onChange({ language: e.target.value })}
          />
          <span className="pill pill-soft">v{lesson.version || 1}</span>
          {dirty && <span className="pill pill-warning">unsaved</span>}
          {saving && <span className="pill pill-soft">autosaving…</span>}
        </div>
      </div>
      <div className="lesson-header__actions">
        <button className="button ghost" onClick={onUndo} disabled={!canUndo}>
          Undo
        </button>
        <button className="button ghost" onClick={onRedo} disabled={!canRedo}>
          Redo
        </button>
        <button className="button" onClick={onSave} disabled={saving}>
          Save backup
        </button>
      </div>
    </header>
  );
}
