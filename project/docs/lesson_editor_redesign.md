# Lesson Editor V2 — Design and Delivery

## 1) UX Flow (One-Page Editor)
- Entry: Admin → Courses → Modules → Lessons → Lesson Editor (`/admin/lessons/{id}` JSON API + SPA shell).
- Sticky lesson header: title, module/course selector, language toggle, status (draft/published), autosave badge, version tag.
- Block canvas: ordered list of blocks with drag handles, collapse/expand, inline edit, preview, delete, duplicate, quick status chip.
- Add Block modal: grid of block types (theory, example, pronunciation, flashcards, quiz, mascot tip, audio, image, assignment) plus templates.
- Inspector panel (right): per-block properties (type-specific content, media URLs, answer keys), metadata (created/updated, author), template apply, undo/redo history.
- Autosave on change (debounced) + manual Save/Publish; undo/redo stored per lesson session; preview button opens read-only rendering.

## 2) Layout (Figma-style description)
- Desktop 12-col grid, max-width 1200px. Split: left 70% block list, right 30% inspector. Padding 24px, gutter 16px.
- Header height 96px; sticky top, white background, subtle shadow. Primary action cluster on the right (Publish/Draft toggle, Preview).
- Block cards: 12px radius, soft shadow, drag handle on the left, status chip on top-right. Accordion for expand/collapse; inline toolbar (duplicate, delete, preview).
- Add Block modal: 720px wide, 2-column grid of type tiles with icon/description; template tabs.
- Mobile: header stacks; inspector becomes bottom sheet; drag via long-press + reorder handles.

## 3) Component Architecture (React-style)
- `LessonEditor` (state: lesson, blocks, selection, draftStatus, autosave tick, undo stack)
  - `LessonHeader`
  - `BlockList`
    - `BlockItem` (collapsed/expanded, selected)
      - `BlockDragHandle`
      - `BlockPreview`
      - `BlockInlineEditor` (renders BaseBlock + type component)
      - `BlockDeleteButton` / `BlockDuplicateButton`
  - `AddBlockButton`
  - `AddBlockModal`
  - `InspectorPanel`
- BaseBlock: shared toolbar + metadata; type components: `BlockTheory`, `BlockExample`, `BlockPronunciation`, `BlockFlashcards`, `BlockQuiz`, `BlockImage`, `BlockAudio`, `BlockAssignment`, `BlockMascotTip`.
- Hooks: `useAutosave(lessonId)`, `useReorder`, `useUndoRedo`, `useLessonQuery`, `useBlockMutations`.
- API client: `BlocksService(lessonId)` wrapping the admin lesson-scoped endpoints.

## 4) Data Model (production-oriented)
- lessons: `id`, `module_id` (FK), `title`, `description`, `order`, `status` (draft/published/archived), `language`, `version`, `created_at`, `updated_at`.
- blocks: `id`, `lesson_id` (FK NOT NULL), `block_type` (enum guard; API exposes as `type`), `order` (unique per lesson), `content` (JSON), `created_at`, `updated_at`.
- Constraints: `UNIQUE (lesson_id, order)`, block type guard (enum/check/trigger per DB), FK on `lesson_id`. Ordering normalized after every mutation.

## 5) Backend API (implemented in `app/routers/lesson_editor_api.py`)
- `GET /admin/lessons/{lesson_id}` → lesson with ordered blocks.
- `GET /admin/lessons/{lesson_id}/blocks` → ordered blocks.
- `POST /admin/lessons/{lesson_id}/blocks` body `{type, content, insert_after?}` → 201 block (auto lesson_id/order).
- `PATCH /admin/lessons/{lesson_id}/blocks/{block_id}` body `{content?, type?, order?}` → 200 block; clamps and shifts order.
- `DELETE /admin/lessons/{lesson_id}/blocks/{block_id}` → 204; re-normalizes order.
- `POST /admin/lessons/{lesson_id}/blocks/reorder` body `{order:[ids]}` → 204; validates exact permutation.
- `POST /admin/lessons/{lesson_id}/blocks/{block_id}/duplicate` → 201 duplicate inserted after source.
- `PATCH /admin/lessons/{lesson_id}` body `{title?, description?, status?, language?, version?}` → 200 lesson.
- Auth: admin only (FastAPI dependency `require_admin`). Idempotency suggested via client `Idempotency-Key` header for POST/duplicate.

## 6) Migration & Data Repair (see `alembic/versions/0002_lesson_editor_overhaul.py`)
- Adds lesson columns: `status`, `language`, `version`, timestamps.
- Adds block timestamps.
- Re-sequences block orders densely per lesson.
- Creates unique index on `(lesson_id, order)`.
- Block type enforcement: DB check (Postgres) or SQLite triggers guarding allowed types.
- Orphan fix: creates system course/module/lesson “Unassigned Blocks” and attaches any `lesson_blocks` with `lesson_id IS NULL`.

## 7) Block Content Schemas (JSON)
- Base: `{ "type": "<enum>", "content": { ... } }`
- Theory: `{ "rich_text": "string", "attachments": ["uri"?] }`
- Example: `{ "sentence": "string", "translation": "string", "notes": "string" }`
- Pronunciation: `{ "phrase": "string", "phonetics": "string", "audio_url": "uri" }`
- Flashcards: `{ "cards": [{ "front": "string", "back": "string", "image_url": "uri?", "audio_url": "uri?" }] }`
- Quiz: `{ "question": "string", "options": [{ "text": "string", "is_correct": bool }], "explanation": "string?" }`
- Image: `{ "url": "uri", "caption": "string?", "alt": "string?" }`
- Audio: `{ "url": "uri", "transcript": "string?" }`
- Assignment: `{ "prompt": "string", "rubric": "string?", "max_score": int?, "submission_type": "text|upload|link" }`
- MascotTip: `{ "tip": "string", "tone": "friendly|encouraging|formal", "icon": "string" }`

## 8) Request/Response Examples
- Create block: `POST /admin/lessons/42/blocks` body `{"type":"quiz","content":{"question":"What is ...?","options":[{"text":"A","is_correct":false},{"text":"B","is_correct":true}]}}` → `201 {"id":9,"lesson_id":42,"type":"quiz","order":5,"content":{...},"created_at":"...","updated_at":"..."}`.
- Reorder: `POST /admin/lessons/42/blocks/reorder` body `{"order":[4,9,1,3]}` → `204`.
- Lesson fetch: `GET /admin/lessons/42` → `{"id":42,"title":"Vowels","status":"draft","language":"kk","blocks":[{"id":4,...}],"updated_at":"...","version":7}`.
- Duplicate: `POST /admin/lessons/42/blocks/7/duplicate` → `201 new block after #7`.

## 9) Error Handling (standardized)
- 400 `invalid_insert_after` or bad payload.
- 401 unauthorized, 403 forbidden (admin dependency).
- 404 lesson/block not found.
- 409 `order_mismatch` for reorder permutations or unique order violation.
- 422 `unsupported_block_type` when type not in enum.
- 500 server_error; include `trace_id` in logs.

## 10) Operational Notes
- Autosave: debounce PATCH to lesson/blocks; show “Saved” with timestamp. Keep undo stack client-side plus optional server-side version increments.
- Draft/Publish: `status` column drives visibility; publishing should bump `version` and optionally snapshot to `lesson_versions` table (future extension).
- Ordering: server normalizes after create/update/delete; client should optimistically reorder but rely on server truth.
- Cleanup: dummy “Unassigned Blocks” lesson isolates bad data; periodic job can notify admins to triage and delete/assign properly.
