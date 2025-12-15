const BLOCK_TYPES = [
  { type: "theory", label: "Theory", desc: "Longform text" },
  { type: "example", label: "Examples", desc: "KZ/RU paired rows" },
  { type: "pronunciation", label: "Pronunciation", desc: "Words to read aloud" },
  { type: "flashcards", label: "Flashcards", desc: "Reference flashcard ids" },
  { type: "quiz", label: "Quiz", desc: "Reference quiz ids" },
  { type: "image", label: "Image", desc: "Hero or inline image" },
  { type: "audio", label: "Audio", desc: "Audio URL + transcript" },
  { type: "assignment", label: "Assignment", desc: "Prompt + rubric" },
  { type: "mascot_tip", label: "Mascot tip", desc: "Inline mascot callout" },
];

export default function AddBlockModal({ onClose, onSelect }) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">
          <div>
            <p className="eyebrow">Block templates</p>
            <h3>Add a block</h3>
          </div>
          <button className="button ghost" onClick={onClose}>
            Close
          </button>
        </div>
        <div className="block-grid">
          {BLOCK_TYPES.map((item) => (
            <button key={item.type} className="block-tile" onClick={() => onSelect(item.type)}>
              <div className="tile-meta">
                <span className="pill pill-soft">{item.label}</span>
                <p className="muted small">{item.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
