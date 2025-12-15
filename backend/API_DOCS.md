# QazaqMentor API (expanded)

## Student
- `GET /api/lessons/{id}` — вернуть урок с упорядоченными блоками (`video`, `theory`, `flashcards`, `pronunciation`, `audio_task`, `quiz`, `lesson_test`, `theory_quiz`).
- `POST /api/progress/block-finished` — отметить блок завершённым. Body: `{lesson_id, block_id, status?, time_spent?}`.
- `POST /api/pronunciation/check` — сверка произношения. Form/Data: `lesson_id`, optional `block_id`, optional `word`, `audio_base64` **или** file `audio`. Возврат: `{score, comment, reference, transcript}`.
- `POST /api/audio-task/submit` — ответ на аудио-задание. Body: `{block_id, selected_option?, answer?}`. Возврат: `{correct, feedback, expected?}`.

## Admin
- `POST /api/admin/lessons/{id}/blocks` — создать блок (type в `BLOCK_TYPE_CHOICES`, data validated). 
- `PUT /api/admin/blocks/{id}` — обновить тип/контент/порядок блока.
- `DELETE /api/admin/blocks/{id}` — мягкое удаление блока.
- `GET /api/admin/lessons/{id}/preview` — детальный просмотр урока (включая блоки) в статусе draft.

## Block payloads
- `audio_task`: `{audio_url, transcript, options?, correct_answer, answer_type(text|multiple_choice), feedback?}`.
- `pronunciation`: `{phrase|word, sample_audio_url?, expected_pronunciation?}`.
- Остальные типы — совместимы с прежними (`video`, `theory`, `flashcards`, `quiz`, `lesson_test`, etc.).

## Pronunciation scoring
Используется Google Cloud Speech-to-Text (язык `kk-KZ`): транскрибируется эталонный и пользовательский аудио, далее cosine similarity по токенам → `score (0–100)` и `comment`. Если эталонного аудио нет, используется текст из блока/параметра `word`.

## Progress storage
`lesson_progress.details.blocks[block_id]` фиксирует завершённые блоки; `audio_tasks` и `pronunciation` истории находятся в `details`.

> Зависимости: добавлен `google-cloud-speech`. Не удалены старые эндпоинты; все новые маршруты подключены в `main.py`.
