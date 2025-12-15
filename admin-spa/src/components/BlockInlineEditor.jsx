import { useEffect, useMemo, useState } from "react";

export default function BlockInlineEditor({ block, onChange }) {
  const [local, setLocal] = useState(block.content || {});

  useEffect(() => {
    setLocal(block.content || {});
  }, [block.id, block.type, block.content]);

  const updateField = (patch) => {
    const next = { ...local, ...patch };
    setLocal(next);
    onChange(next);
  };

  const renderExamples = () => {
    const examples = local.examples || [];
    const updateExample = (idx, patch) => {
      const nextExamples = examples.map((row, i) => (i === idx ? { ...row, ...patch } : row));
      updateField({ examples: nextExamples });
    };
    return (
      <div className="stack">
        {examples.map((row, idx) => (
          <div className="two-col" key={idx}>
            <input
              value={row.kz || ""}
              placeholder="KZ"
              onChange={(e) => updateExample(idx, { kz: e.target.value })}
            />
            <input
              value={row.ru || ""}
              placeholder="RU"
              onChange={(e) => updateExample(idx, { ru: e.target.value })}
            />
          </div>
        ))}
        <button
          className="button ghost"
          type="button"
          onClick={() => updateField({ examples: [...examples, { kz: "", ru: "" }] })}
        >
          + Add example row
        </button>
      </div>
    );
  };

  const renderAssignment = () => (
    <div className="stack">
      <textarea
        value={local.prompt || ""}
        placeholder="Prompt"
        onChange={(e) => updateField({ prompt: e.target.value })}
      />
      <textarea
        value={local.rubric || ""}
        placeholder="Rubric"
        onChange={(e) => updateField({ rubric: e.target.value })}
      />
      <div className="two-col">
        <input
          type="number"
          min="0"
          value={local.max_score ?? ""}
          placeholder="Max score"
          onChange={(e) => updateField({ max_score: e.target.value ? Number(e.target.value) : null })}
        />
        <select
          value={local.submission_type || "text"}
          onChange={(e) => updateField({ submission_type: e.target.value })}
        >
          <option value="text">Text</option>
          <option value="file">File upload</option>
          <option value="audio">Audio</option>
        </select>
      </div>
    </div>
  );

  const idListInput = (field, label) => (
    <div className="stack">
      <label className="muted small">{label}</label>
      <input
        value={(local[field] || []).join(",")}
        placeholder="IDs separated by comma"
        onChange={(e) => {
          const ids = e.target.value
            .split(",")
            .map((v) => Number(v.trim()))
            .filter(Boolean);
          updateField({ [field]: ids });
        }}
      />
    </div>
  );

  const renderEditor = () => {
    switch (block.type) {
      case "theory":
        return (
          <div className="stack">
            <input
              value={local.heading || ""}
              placeholder="Heading"
              onChange={(e) => updateField({ heading: e.target.value })}
            />
            <textarea
              value={local.body || ""}
              placeholder="Body text"
              rows={5}
              onChange={(e) => updateField({ body: e.target.value })}
            />
          </div>
        );
      case "example":
        return (
          <div className="stack">
            <input
              value={local.prompt || ""}
              placeholder="Prompt"
              onChange={(e) => updateField({ prompt: e.target.value })}
            />
            {renderExamples()}
          </div>
        );
      case "pronunciation":
        return (
          <textarea
            value={(local.words || []).join("\n")}
            rows={4}
            placeholder="One word per line"
            onChange={(e) => updateField({ words: e.target.value.split("\n").filter(Boolean) })}
          />
        );
      case "flashcards":
        return idListInput("flashcard_ids", "Flashcard IDs");
      case "quiz":
        return idListInput("quiz_ids", "Quiz IDs");
      case "image":
        return (
          <div className="stack">
            <input
              value={local.url || ""}
              placeholder="Image URL"
              onChange={(e) => updateField({ url: e.target.value })}
            />
            <input
              value={local.caption || ""}
              placeholder="Caption"
              onChange={(e) => updateField({ caption: e.target.value })}
            />
          </div>
        );
      case "audio":
        return (
          <div className="stack">
            <input
              value={local.url || ""}
              placeholder="Audio URL"
              onChange={(e) => updateField({ url: e.target.value })}
            />
            <textarea
              value={local.transcript || ""}
              placeholder="Transcript"
              onChange={(e) => updateField({ transcript: e.target.value })}
            />
          </div>
        );
      case "assignment":
        return renderAssignment();
      case "mascot_tip":
        return (
          <div className="stack">
            <textarea
              value={local.text || ""}
              placeholder="Mascot text"
              onChange={(e) => updateField({ text: e.target.value })}
            />
            <input
              value={local.icon || ""}
              placeholder="Icon (emoji or short code)"
              onChange={(e) => updateField({ icon: e.target.value })}
            />
          </div>
        );
      default:
        return <p className="muted small">Unsupported block</p>;
    }
  };

  const filler = useMemo(() => renderEditor(), [block.type, local]);

  return <div className="inline-editor">{filler}</div>;
}
