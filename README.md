# Qazaq EdTech Platform

Учебная платформа для казахского языка на FastAPI + Jinja2 + SQLAlchemy. Проект готов для локального запуска на SQLite и последующей миграции на Postgres.

## Быстрый старт
- Перейти в каталог проекта: `cd project`
- Установить зависимости: `pip install -r requirements.txt`
- Применить миграции и заполнить тестовыми данными: `alembic upgrade head`
- Запуск: `uvicorn app.main:app --reload`

## Админ
- Дефолтный админ после миграции: `admin@example.com` / `admin123`
- Панель: `/admin` (роли: поле `role` в таблице users)

## Технологии
- Backend: FastAPI, SQLAlchemy, Alembic
- Frontend: Jinja2 + Bootstrap 5
- БД: SQLite (по умолчанию), совместимо с Postgres

## Структура
- `app/main.py` — точка входа FastAPI, подключение роутов и шаблонов
- `app/models` — SQLAlchemy модели
- `app/schemas` — Pydantic-схемы
- `app/services` — доменная логика
- `app/routers` — маршруты для страниц и действий
- `app/templates` — Jinja-шаблоны, `components/mascot_tip.html` для маскота
- `alembic` — миграции и заполнение тестовыми данными
# qazaq
