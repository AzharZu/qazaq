# Qazaq EdTech Platform

Учебная платформа для казахского языка: чистый FastAPI JSON API + две SPA (студент `/app`, админ `/admin`). Legacy Jinja маршруты удалены, весь рендеринг через SPA.

## Новая структура
```
backend/app/       # основной бекенд (FastAPI, схемы, сервисы)
backend/alembic/   # миграции
student-spa/       # фронт студента (Vite), раздаётся по /app
admin-spa/         # фронт админа, раздаётся по /admin
qazaq.db           # SQLite по умолчанию (можно заменить DATABASE_URL)
```

**project/ is legacy, use backend/.**

## Быстрый старт (dev)
- Установить зависимости: `pip install -r backend/requirements.txt`
- Применить миграции: `cd backend && alembic upgrade head`
- Собрать SPA (если нужно): `cd student-spa && npm install && npm run build` и аналогично для `admin-spa`
- Запуск API: `cd backend && GEMINI_API_KEY=... uvicorn app.main:app --reload`
  - CORS открыт (`*`), сессии через cookie `session`.

## Ключевые API
- Auth: `POST /api/auth/signup`, `/api/auth/login`, `/api/auth/logout`
- Курсы: `/api/courses`, `/api/courses/{slug}`, `/api/modules`, `/api/modules/{id}`, `/api/lessons/{id}`
- Прогресс: `/api/progress`
- Плейсмент: `/api/placement/start|next|answer|result`
- Словарь/игры: `/api/vocabulary`, `/api/vocabulary/game/{mode}`, `/api/vocabulary/game/{mode}/check`, `/api/vocabulary/tts`
- AutoChecker: `POST /api/autochecker` (`text`, `mode`, `language`)

## Деплой
1) `python -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt`
2) `cd backend && alembic upgrade head`
3) Собрать SPA: `cd student-spa && npm ci && npm run build` (и `admin-spa`)
4) Запуск: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
5) ENV: `GEMINI_API_KEY`, `SECRET_KEY`, `DATABASE_URL` (Postgres/SQLite), опционально `ALLOWED_ORIGINS`.
6) Проксировать `/api`, `/app`, `/admin`; статика SPA уже монтируется приложением.
