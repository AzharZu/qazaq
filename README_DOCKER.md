# Docker Setup для Qazaq Platform

## 🚀 Быстрый старт

### Production (полный запуск)
```bash
./docker-start.sh
```

### Development (только backend + БД, frontend локально)
```bash
docker-compose -f docker-compose.dev.yml up -d
```

Затем запустите frontend отдельно:
```bash
cd admin-spa && npm run dev
```

## 📦 Оптимизации

### 1. BuildKit ускорение
Используется BuildKit для параллельной сборки и кэширования:
- Первая сборка: ~5-10 минут
- Последующие сборки: ~30 секунд (благодаря кэшу слоев)

### 2. Кэширование слоев Docker
- `requirements.txt` и `package.json` копируются отдельно
- Зависимости устанавливаются в отдельном слое
- Код приложения копируется последним (часто меняется)

### 3. .dockerignore
Исключены ненужные файлы из контекста сборки:
- `node_modules`
- `__pycache__`
- `.git`
- Логи и временные файлы

### 4. Multi-stage builds
Admin SPA использует multi-stage build:
- Stage 1: Установка зависимостей
- Stage 2: Сборка приложения
- Stage 3: Nginx (только статика)

## 🔧 Полезные команды

```bash
# Просмотр логов
docker-compose logs -f backend
docker-compose logs -f admin-spa

# Перезапуск сервиса
docker-compose restart backend

# Пересборка без кэша
docker-compose build --no-cache backend

# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

## 🌐 Доступ к сервисам

- **Admin Panel**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs
- **Main Site**: http://localhost (через nginx)
- **Database**: localhost:5432 (только в dev режиме)

## 🐛 Troubleshooting

### Backend не запускается
```bash
docker-compose logs backend
docker exec -it qazaq_backend bash
```

### Admin SPA не собирается
```bash
docker-compose build --no-cache admin-spa
docker-compose logs admin-spa
```

### Проблемы с базой данных
```bash
docker-compose down -v  # Удалить volumes
docker-compose up -d postgres
```

## ⚡ Ускорение для разработки

Используйте `docker-compose.dev.yml` для:
- Hot reload backend (uvicorn --reload)
- Локальный запуск frontend (npm run dev)
- Быстрый доступ к БД через порт 5432
