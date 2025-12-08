import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLessons } from "../api/lessons";

const STATUS_COLORS = {
  draft: "muted",
  published: "success",
  archived: "warning",
};

function LessonCard({ lesson }) {
  const statusClass = STATUS_COLORS[lesson.status] || "info";
  return (
    <div className="lesson-card">
      <div className="lesson-card__meta">
        <span className={`pill pill-${statusClass}`}>{lesson.status}</span>
        <span className="pill pill-soft">{lesson.language}</span>
        <span className="pill pill-soft">#{lesson.id}</span>
      </div>
      <h3>{lesson.title}</h3>
      <p className="muted">Module #{lesson.module_id} · Order {lesson.order}</p>
      <div className="lesson-card__actions">
        <Link className="button primary" to={`/lessons/${lesson.id}/editor`}>
          Open Editor
        </Link>
        <Link className="button ghost" to={`/lessons/${lesson.id}/editor`} state={{ focus: "meta" }}>
          Metadata
        </Link>
      </div>
    </div>
  );
}

export default function LessonsList() {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLessons();
      setLessons(data);
    } catch (err) {
      setError(err.message || "Failed to load lessons");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const grouped = useMemo(() => {
    return lessons.reduce((acc, lesson) => {
      const key = lesson.module_id;
      acc[key] = acc[key] || [];
      acc[key].push(lesson);
      return acc;
    }, {});
  }, [lessons]);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin · Lessons</p>
          <h1>Lesson Library</h1>
          <p className="muted">
            Manage lessons and launch the Notion-style editor. Everything under /admin is powered by this SPA.
          </p>
        </div>
        <div className="actions">
          <button className="button ghost" onClick={load} disabled={loading}>
            Refresh
          </button>
          <Link className="button primary" to="/lessons/1/editor">
            Jump to Lesson 1
          </Link>
        </div>
      </header>
      {error && <div className="banner danger">{error}</div>}
      {loading ? (
        <div className="loading">Loading lessons…</div>
      ) : (
        <div className="lesson-grid">
          {Object.keys(grouped).length === 0 && <div className="muted">No lessons found.</div>}
          {Object.entries(grouped).map(([moduleId, items]) => (
            <section key={moduleId} className="module-stack">
              <div className="module-header">
                <span className="pill pill-soft">Module {moduleId}</span>
                <span className="muted small">{items.length} lessons</span>
              </div>
              <div className="lesson-row">
                {items.map((lesson) => (
                  <LessonCard key={lesson.id} lesson={lesson} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
