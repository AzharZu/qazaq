function formatDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch (e) {
    return String(value);
  }
}

export default function InspectorPanel({ block, onDelete, onDuplicate }) {
  if (!block) {
    return (
      <aside className="inspector">
        <p className="muted">Select a block to inspect its metadata.</p>
      </aside>
    );
  }

  return (
    <aside className="inspector">
      <div className="inspector__header">
        <div>
          <p className="eyebrow">Inspector</p>
          <h3>Block #{block.id}</h3>
          <p className="muted small">{block.type}</p>
        </div>
        <div className="vstack">
          <button className="button ghost" onClick={onDuplicate}>
            Duplicate
          </button>
          <button className="button ghost danger" onClick={onDelete}>
            Delete
          </button>
        </div>
      </div>
      <div className="inspector__section">
        <p className="muted small">Order</p>
        <div className="pill pill-soft">#{block.order}</div>
      </div>
      <div className="inspector__section">
        <p className="muted small">Created</p>
        <p>{formatDate(block.created_at)}</p>
      </div>
      <div className="inspector__section">
        <p className="muted small">Updated</p>
        <p>{formatDate(block.updated_at)}</p>
      </div>
      <div className="inspector__section">
        <p className="muted small">Content</p>
        <pre className="code-block">{JSON.stringify(block.content, null, 2)}</pre>
      </div>
    </aside>
  );
}
