import { useMemo, useState } from "react";
import BlockInlineEditor from "./BlockInlineEditor.jsx";

const BLOCK_TYPE_LABELS = {
  theory: "Theory",
  example: "Example",
  pronunciation: "Pronunciation",
  flashcards: "Flashcards",
  quiz: "Quiz",
  image: "Image",
  audio: "Audio",
  assignment: "Assignment",
  mascot_tip: "Mascot Tip",
};

function Preview({ block }) {
  const content = block.content || {};
  switch (block.type) {
    case "theory":
      return <p className="muted small">{content.heading || content.body || "No content"}</p>;
    case "example":
      return (
        <p className="muted small">
          {(content.examples || []).length} row(s) · {content.prompt || "Examples"}
        </p>
      );
    case "pronunciation":
      return <p className="muted small">{(content.words || []).join(", ") || "Add words"}</p>;
    case "flashcards":
      return <p className="muted small">{(content.flashcard_ids || []).length} flashcard ids</p>;
    case "quiz":
      return <p className="muted small">{(content.quiz_ids || []).length} quiz ids</p>;
    case "image":
      return <p className="muted small">{content.url || "Add image url"}</p>;
    case "audio":
      return <p className="muted small">{content.url || "Add audio url"}</p>;
    case "assignment":
      return <p className="muted small">{content.prompt || "Assignment prompt"}</p>;
    case "mascot_tip":
      return <p className="muted small">{content.text || "Tip text"}</p>;
    default:
      return <p className="muted small">Unsupported block</p>;
  }
}

export default function BlockItem({
  block,
  index,
  selected,
  dragging,
  onSelect,
  onChangeContent,
  onChangeType,
  onDuplicate,
  onDelete,
  dragHandleProps,
  draggableProps,
  innerRef,
}) {
  const [expanded, setExpanded] = useState(true);
  const label = useMemo(() => BLOCK_TYPE_LABELS[block.type] || block.type, [block.type]);

  return (
    <div
      className={`block-card ${selected ? "is-selected" : ""} ${dragging ? "is-dragging" : ""}`}
      onClick={onSelect}
      ref={innerRef}
      {...draggableProps}
    >
      <div className="block-toolbar">
        <div className="drag-handle" {...dragHandleProps} aria-label="Drag block">
          ☰
        </div>
        <div className="block-toolbar__meta">
          <span className="pill pill-soft">{label}</span>
          <Preview block={block} />
        </div>
        <div className="block-toolbar__actions">
          <select value={block.type} onChange={(e) => onChangeType(e.target.value)}>
            {Object.keys(BLOCK_TYPE_LABELS).map((type) => (
              <option key={type} value={type}>
                {BLOCK_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
          <button className="ghost-link" onClick={(e) => (e.stopPropagation(), setExpanded((v) => !v))}>
            {expanded ? "Collapse" : "Expand"}
          </button>
          <button className="ghost-link" onClick={(e) => (e.stopPropagation(), onDuplicate())}>
            Duplicate
          </button>
          <button className="ghost-link danger" onClick={(e) => (e.stopPropagation(), onDelete())}>
            Delete
          </button>
        </div>
      </div>
      {expanded && (
        <BlockInlineEditor
          block={block}
          onChange={(next) => {
            onChangeContent(next);
          }}
        />
      )}
    </div>
  );
}
