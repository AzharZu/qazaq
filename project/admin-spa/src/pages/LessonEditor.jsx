import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  createBlock,
  deleteBlock,
  duplicateBlock,
  reorderBlocks,
  updateBlock,
} from "../api/blocks";
import { fetchLesson, updateLesson } from "../api/lessons";
import AddBlockModal from "../components/AddBlockModal.jsx";
import BlockList from "../components/BlockList.jsx";
import InspectorPanel from "../components/InspectorPanel.jsx";
import LessonHeader from "../components/LessonHeader.jsx";

const BLOCK_TEMPLATES = {
  theory: { heading: "New note", body: "" },
  example: { prompt: "Example prompt", examples: [{ kz: "", ru: "" }] },
  pronunciation: { words: [""] },
  flashcards: { flashcard_ids: [] },
  quiz: { quiz_ids: [] },
  image: { url: "", caption: "" },
  audio: { url: "", transcript: "" },
  assignment: { prompt: "", rubric: "", max_score: null, submission_type: "text" },
  mascot_tip: { text: "Quick tip", icon: "" },
};

const deepCopy = (value) => JSON.parse(JSON.stringify(value));
const normalizeBlock = (block) => ({
  ...block,
  type: block.type || block.block_type,
  content: block.content || {},
});
const pickLessonPatch = (lesson) => ({
  title: lesson.title,
  description: lesson.description,
  status: lesson.status,
  language: lesson.language,
  version: lesson.version,
});

export default function LessonEditor() {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [history, setHistory] = useState([]);
  const [future, setFuture] = useState([]);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [pendingLessonPatch, setPendingLessonPatch] = useState({});
  const [pendingBlocks, setPendingBlocks] = useState(new Map());
  const [pendingReorder, setPendingReorder] = useState(false);

  const selectedBlock = useMemo(() => blocks.find((b) => b.id === selectedId), [blocks, selectedId]);

  const loadLesson = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLesson(lessonId);
      const normalized = (data.blocks || []).map(normalizeBlock);
      const { blocks: _blocks, ...rest } = data;
      setLesson(rest);
      setBlocks(normalized);
      setHistory([]);
      setFuture([]);
      setPendingBlocks(new Map());
      setPendingLessonPatch({});
      setPendingReorder(false);
      setDirty(false);
      if (normalized.length) {
        setSelectedId(normalized[0].id);
      }
    } catch (err) {
      setError(err.message || "Failed to load lesson");
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    loadLesson();
  }, [loadLesson]);

  const pushHistory = useCallback(() => {
    if (!lesson) return;
    const snapshot = {
      lesson: { ...lesson },
      blocks: deepCopy(blocks),
    };
    setHistory((prev) => [...prev.slice(-19), snapshot]);
    setFuture([]);
  }, [lesson, blocks]);

  const handleLessonChange = (patch) => {
    pushHistory();
    setLesson((prev) => ({ ...prev, ...patch }));
    setPendingLessonPatch((prev) => ({ ...prev, ...patch }));
    setDirty(true);
  };

  const handleBlockContentChange = (blockId, content, typeOverride) => {
    pushHistory();
    setBlocks((prev) => {
      const updated = prev.map((block) =>
        block.id === blockId ? { ...block, content, type: typeOverride || block.type } : block,
      );
      const nextBlock = updated.find((b) => b.id === blockId);
      setPendingBlocks((prevMap) => {
        const next = new Map(prevMap);
        next.set(blockId, { content: nextBlock.content, type: nextBlock.type });
        return next;
      });
      return updated;
    });
    setDirty(true);
  };

  const handleBlockTypeChange = (blockId, nextType) => {
    const template = deepCopy(BLOCK_TEMPLATES[nextType] || {});
    handleBlockContentChange(blockId, template, nextType);
  };

  const handleAddBlock = async (type) => {
    if (!lesson) return;
    setShowModal(false);
    try {
      const created = await createBlock(lesson.id, { type, content: deepCopy(BLOCK_TEMPLATES[type] || {}) });
      const normalized = normalizeBlock(created);
      pushHistory();
      setBlocks((prev) => [...prev, normalized]);
      setSelectedId(normalized.id);
    } catch (err) {
      setError(err.message || "Unable to add block");
    }
  };

  const handleDeleteBlock = async (blockId) => {
    pushHistory();
    try {
      await deleteBlock(blockId);
      setBlocks((prev) => prev.filter((b) => b.id !== blockId));
      setPendingBlocks((prev) => {
        const next = new Map(prev);
        next.delete(blockId);
        return next;
      });
      setPendingReorder(true);
      setDirty(true);
    } catch (err) {
      setError(err.message || "Unable to delete block");
    }
  };

  const handleDuplicateBlock = async (blockId) => {
    pushHistory();
    try {
      const clone = await duplicateBlock(blockId);
      const normalized = normalizeBlock(clone);
      setBlocks((prev) => {
        const idx = prev.findIndex((b) => b.id === blockId);
        const next = [...prev];
        next.splice(idx + 1, 0, normalized);
        return next;
      });
      setPendingReorder(true);
      setDirty(true);
    } catch (err) {
      setError(err.message || "Unable to duplicate block");
    }
  };

  const handleReorder = ({ sourceIndex, destinationIndex }) => {
    if (sourceIndex === destinationIndex) return;
    pushHistory();
    setBlocks((prev) => {
      const next = [...prev];
      const [moved] = next.splice(sourceIndex, 1);
      next.splice(destinationIndex, 0, moved);
      return next.map((b, idx) => ({ ...b, order: idx + 1 }));
    });
    setPendingReorder(true);
    setDirty(true);
  };

  const performSave = useCallback(
    async (mode = "auto") => {
      if (!lesson) return;
      if (!dirty && mode === "auto") return;
      setSaving(true);
      setError(null);
      try {
        if (Object.keys(pendingLessonPatch).length) {
          const payload = { ...pendingLessonPatch };
          if (mode === "manual") {
            payload.version = (lesson.version || 1) + 1;
          }
          const updated = await updateLesson(lesson.id, payload);
          const { blocks: _serverBlocks, ...rest } = updated;
          setLesson((prev) => ({ ...prev, ...rest }));
          setPendingLessonPatch({});
        }

        const entries = Array.from(pendingBlocks.entries());
        for (const [id, payload] of entries) {
          const saved = await updateBlock(id, payload);
          const normalized = normalizeBlock(saved);
          setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, ...normalized } : b)));
        }
        if (entries.length) {
          setPendingBlocks(new Map());
        }

        if (pendingReorder) {
          await reorderBlocks(lesson.id, blocks.map((b) => b.id));
          setPendingReorder(false);
        }

        setDirty(false);
      } catch (err) {
        setError(err.message || "Save failed");
      } finally {
        setSaving(false);
      }
    },
    [lesson, pendingLessonPatch, pendingBlocks, pendingReorder, blocks, dirty],
  );

  useEffect(() => {
    if (!dirty) return;
    const timer = setTimeout(() => performSave("auto"), 1500);
    return () => clearTimeout(timer);
  }, [dirty, performSave]);

  const handleUndo = () => {
    if (!history.length) return;
    const previous = history[history.length - 1];
    setHistory((prev) => prev.slice(0, -1));
    setFuture((prev) => [{ lesson: { ...lesson }, blocks: deepCopy(blocks) }, ...prev]);
    setLesson(previous.lesson);
    setBlocks(previous.blocks);
    const map = new Map(previous.blocks.map((b) => [b.id, { content: b.content, type: b.type }]));
    setPendingBlocks(map);
    setPendingLessonPatch(pickLessonPatch(previous.lesson));
    setPendingReorder(true);
    setDirty(true);
  };

  const handleRedo = () => {
    if (!future.length) return;
    const nextState = future[0];
    setFuture((prev) => prev.slice(1));
    setHistory((prev) => [...prev, { lesson: { ...lesson }, blocks: deepCopy(blocks) }]);
    setLesson(nextState.lesson);
    setBlocks(nextState.blocks);
    const map = new Map(nextState.blocks.map((b) => [b.id, { content: b.content, type: b.type }]));
    setPendingBlocks(map);
    setPendingLessonPatch(pickLessonPatch(nextState.lesson));
    setPendingReorder(true);
    setDirty(true);
  };

  if (loading) {
    return (
      <div className="page">
        <p className="muted">Loading lesson…</p>
      </div>
    );
  }

  if (error && !lesson) {
    return (
      <div className="page">
        <div className="banner danger">{error}</div>
        <button className="button ghost" onClick={loadLesson}>
          Retry
        </button>
      </div>
    );
  }

  if (!lesson) return null;

  return (
    <div className="page">
      <div className="crumbs">
        <Link to="/lessons" className="ghost-link">
          ← Lessons
        </Link>
        <span className="muted">Lesson #{lesson.id}</span>
      </div>
      <LessonHeader
        lesson={lesson}
        saving={saving}
        dirty={dirty}
        onChange={handleLessonChange}
        onSave={() => performSave("manual")}
        onUndo={handleUndo}
        onRedo={handleRedo}
        canUndo={history.length > 0}
        canRedo={future.length > 0}
      />
      {error && <div className="banner danger">{error}</div>}
      <div className="editor-layout">
        <div className="block-column">
          <BlockList
            blocks={blocks}
            onChangeContent={handleBlockContentChange}
            onChangeType={handleBlockTypeChange}
            onDuplicate={handleDuplicateBlock}
            onDelete={handleDeleteBlock}
            onSelect={setSelectedId}
            selectedId={selectedId}
            onReorder={handleReorder}
          />
          <div className="inline-actions">
            <button className="button ghost" onClick={() => setShowModal(true)}>
              + Add block
            </button>
            <button className="button" onClick={() => performSave("manual")} disabled={saving}>
              Save snapshot
            </button>
            {saving && <span className="muted small">Saving…</span>}
          </div>
        </div>
        <InspectorPanel
          block={selectedBlock}
          onDelete={() => selectedBlock && handleDeleteBlock(selectedBlock.id)}
          onDuplicate={() => selectedBlock && handleDuplicateBlock(selectedBlock.id)}
        />
      </div>
      {showModal && <AddBlockModal onClose={() => setShowModal(false)} onSelect={handleAddBlock} />}
    </div>
  );
}
