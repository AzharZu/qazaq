# 🐛 ДОПОЛНИТЕЛЬНЫЕ ОШИБКИ И ПРОБЛЕМЫ

**Дата:** 19 декабря 2025  
**Раздел:** Другие ошибки, найденные при аудите (не связанные со словарем)

---

## 🔍 ОБНАРУЖЕННЫЕ ДОПОЛНИТЕЛЬНЫЕ ПРОБЛЕМЫ

### А1: Возможное несоответствие типов данных

**Где:** Backend вероятно возвращает разные типы для одного поля

**Файл:** `backend/app/models/vocabulary.py` (предположительно)

**Проблема:**
- Может быть, что поле `word` иногда `null`
- Может быть, что `translation` иногда пусто
- Это приводит к ошибкам на frontend

**Рекомендация:**
```python
# В моделе VocabularyWord добавить валидацию:
from pydantic import validator

class VocabularyWord(BaseModel):
    id: int
    user_id: int
    word: str  # ← Должно быть NOT NULL в БД
    translation: str  # ← Должно быть NOT NULL в БД
    
    @validator('word', 'translation', pre=True, always=True)
    def empty_to_none(cls, v):
        if v == '' or v is None:
            raise ValueError('Cannot be empty')
        return v
```

**Проверить:**
```sql
-- В PostgreSQL:
SELECT * FROM vocabulary_words WHERE word IS NULL OR translation IS NULL;
-- Результат должен быть пуст
```

---

### А2: Отсутствует protection от SQL injection в некоторых запросах

**Где:** Может быть в lesson_detail, dictionary endpoints

**Проблема:**
- Если используются raw SQL запросы вместо ORM
- Параметры не экранируются

**Как проверить:**
```python
# ❌ ПЛОХО:
query = f"SELECT * FROM lessons WHERE id = {lesson_id}"
result = session.execute(query)

# ✅ ХОРОШО:
query = select(Lesson).where(Lesson.id == lesson_id)
result = session.execute(query)
```

**Рекомендация:**
- Использовать только SQLAlchemy ORM
- Избегать f-strings в SQL запросах

---

### А3: Race condition при быстром открытии нескольких уроков

**Где:** Frontend загружает словарь несколько раз подряд

**Проблема:**
```
Время:     Событие:
t1         Открыть урок 1 → loadWords() #1
t2         Быстро открыть урок 2 → loadWords() #2
t3         Быстро открыть урок 3 → loadWords() #3
t4         Ответы приходят в порядке: #3, #1, #2
t5         Frontend состояние = слова из урока #2 (неправильно!)
```

**Решение:** Использовать AbortController
```typescript
const [controller, setController] = useState<AbortController | null>(null);

useEffect(() => {
  const newController = new AbortController();
  setController(newController);

  const load = async () => {
    const words = await dictionaryApi.getDictionaryWords({
      signal: newController.signal,
    });
    setWords(words);
  };

  load().catch((err) => {
    if (err.name !== 'AbortError') console.error(err);
  });

  return () => newController.abort();
}, []);
```

---

### А4: Возможная утечка памяти в useEffect

**Где:** Компоненты, где используется `loadWords()` и другие async операции

**Проблема:**
```typescript
useEffect(() => {
  loadWords();  // Запрос стартует
  // Компонент unmountится -> запрос завершится → попытка setState
  // ❌ React ошибка: "Can't perform a React state update on an unmounted component"
}, []);
```

**Решение:**
```typescript
useEffect(() => {
  let isMounted = true;

  const load = async () => {
    try {
      const data = await loadWords();
      if (isMounted) {  // ← Проверка перед setState
        setWords(data);
      }
    } catch (err) {
      if (isMounted) {
        setError(err);
      }
    }
  };

  load();

  return () => {
    isMounted = false;  // ← Cleanup
  };
}, []);
```

---

### А5: Проблема с localStorage persistence при logout

**Где:** Frontend, если используется localStorage для хранения токена

**Проблема:**
- Пользователь логинится → токен в localStorage
- Пользователь логинится с другого браузера → СТАРЫЙ токен все еще в памяти
- Возможна конфликтация

**Как проверить:**
```typescript
// В authStore.ts или аналогичном:
export const logout = () => {
  // ✅ ПРАВИЛЬНО: Очистить ВСЕ данные
  localStorage.clear();
  sessionStorage.clear();
  // Очистить все store состояния
  set({ token: null, user: null, words: [] });
};
```

---

### А6: Missing error boundaries в компонентах

**Где:** Главные страницы (lesson, dictionary, profile)

**Проблема:**
- Если компонент выбросит ошибку → вся приложение сломается
- Нет fallback UI

**Решение:** Добавить Error Boundary
```typescript
import React from "react";

class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Error caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div>Что-то пошло не так. Пожалуйста, перезагрузите страницу.</div>;
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
```

**Использование:**
```typescript
<ErrorBoundary>
  <LessonPage />
</ErrorBoundary>
```

---

### А7: Отсутствует validation для входящих данных от API

**Где:** Frontend компоненты, где используются данные из API напрямую

**Проблема:**
```typescript
// ❌ ПЛОХО: Нет проверки структуры данных
const word = words[currentIndex];
return <div>{word.translation}</div>; // Что если word undefined?
```

**Решение:**
```typescript
// ✅ ХОРОШО: Добавить проверки
if (!word) return <div>No word selected</div>;
if (!word.translation) return <div>Translation missing</div>;
return <div>{word.translation}</div>;
```

---

### А8: Нет timeout для длительных API запросов

**Где:** `dictionaryApi.getDictionaryWords()` и другие запросы

**Проблема:**
- Если network медленный, пользователь ждет бесконечно
- Нет feedback'а о loading статусе

**Решение:**
```typescript
// В api файле:
export const dictionaryApi = {
  getDictionaryWords: async (options?: any) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10 сек
    
    try {
      const response = await fetch('/api/dictionary', {
        signal: controller.signal,
        ...options,
      });
      return response.json();
    } finally {
      clearTimeout(timeout);
    }
  },
};
```

---

### А9: Возможные TypeScript errors в некоторых компонентах

**Где:** Нужна полная проверка

**Как проверить:**
```bash
cd student-next
npm run type-check  # Или: npx tsc --noEmit
```

**Решение:** Исправить все ошибки перед deploymentом

---

### А10: Отсутствует validation структуры lesson.blocks

**Где:** `lesson/[id].tsx`, `LessonBlockRenderer.tsx`

**Проблема:**
```typescript
// ❌ ПЛОХО: Может быть undefined
blocks.forEach(block => {
  const type = block.type;  // Что если type undefined?
  renderBlock(type);
});
```

**Решение:**
```typescript
// ✅ ХОРОШО: Добавить проверки
blocks.forEach(block => {
  if (!block || !block.type) {
    console.warn("Invalid block:", block);
    return;
  }
  renderBlock(block.type);
});
```

---

## 📊 СТАТИСТИКА ДОПОЛНИТЕЛЬНЫХ ОШИБОК

| # | Описание | Severity | Файлы |
|---|----------|----------|-------|
| А1 | Типы данных | 🟡 Medium | Все API модели |
| А2 | SQL injection | 🔴 Critical | vocabulary_service.py |
| А3 | Race conditions | 🔴 Critical | DictionaryStore |
| А4 | Memory leaks | 🟡 Medium | Все useEffect |
| А5 | localStorage cleanup | 🟡 Medium | authStore |
| А6 | Error boundaries | 🟡 Medium | Главные компоненты |
| А7 | Data validation | 🟡 Medium | Все компоненты |
| А8 | Request timeout | 🟢 Low | API файлы |
| А9 | TypeScript errors | 🟡 Medium | Все файлы |
| А10 | Block validation | 🟡 Medium | lesson, renderer |

---

## 🎯 ПРИОРИТЕТ ИСПРАВЛЕНИЯ

### Приоритет 1 (DO NOW):
- [ ] А2: SQL injection (если используются raw queries)
- [ ] А3: Race conditions
- [ ] А10: Block validation

### Приоритет 2 (THIS WEEK):
- [ ] А1: Type validation
- [ ] А4: Memory leaks
- [ ] А6: Error boundaries
- [ ] А9: TypeScript errors

### Приоритет 3 (NICE TO HAVE):
- [ ] А5: localStorage cleanup
- [ ] А7: Data validation
- [ ] А8: Request timeout

---

## 🔍 КАК ПРОВЕРИТЬ КАЖДУЮ

### Проверка А1: Типы данных
```bash
# Запросить словарь:
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/dictionary | jq .

# Проверить структуру каждого элемента
# Все ли поля присутствуют? Есть ли null значения?
```

### Проверка А2: SQL Injection
```bash
# В коде backend найти:
grep -r "f\"SELECT" backend/
grep -r "f'SELECT" backend/

# Если найдено - это проблема!
```

### Проверка А3: Race conditions
```typescript
// В DevTools Console:
// 1. Открыть Network tab
// 2. Быстро кликнуть на 3 разных урока подряд
// 3. Посмотреть порядок ответов
// 4. Проверить, правильно ли загружен словарь
```

### Проверка А4: Memory leaks
```bash
# В Chrome DevTools:
# 1. Memory tab
# 2. Take heap snapshot
# 3. Открыть и закрыть компонент несколько раз
# 4. Take another snapshot
# 5. Compare - не должно быть утечек
```

### Проверка А5: localStorage cleanup
```typescript
// Перед logout:
console.log(localStorage.getItem('token'));  // Должен быть token

// После logout:
console.log(localStorage.getItem('token'));  // Должен быть null
```

### Проверка А6-А10: Code review
```bash
# Просто сделать code review всех этих файлов:
- student-next/src/pages/lesson/[id].tsx
- student-next/src/components/LessonBlockRenderer.tsx
- student-next/src/store/authStore.ts
- backend/app/services/vocabulary_service.py
```

---

## 🚀 ДЕЙСТВИЯ

1. **Немедленно:**
   - Проверить использование raw SQL (А2)
   - Добавить AbortController (А3)
   - Добавить валидацию blocks (А10)

2. **На этой неделе:**
   - Type validation (А1)
   - Memory leak checks (А4)
   - Error boundaries (А6)
   - TypeScript checking (А9)

3. **Когда будет время:**
   - localStorage cleanup (А5)
   - Data validation (А7)
   - Request timeout (А8)

---

