# 🔧 КОДЫ ИСПРАВЛЕНИЙ - ГОТОВЫЙ К ИСПОЛЬЗОВАНИЮ

**Дата:** 19 декабря 2025  
**Цель:** Copy-paste готовые исправления для каждого файла

---

## 1️⃣ Исправление: `student-next/src/pages/lesson/[id].tsx`

### УДАЛИТЬ эти строки:

**Строка 9:** Удалить импорт
```typescript
// ❌ УДАЛИТЬ эту строку:
import { useDictionaryStore } from "@/store/dictionaryStore";
```

**Строка 31:** Удалить деструктуризацию
```typescript
// ❌ УДАЛИТЬ эту строку:
const { loadWords } = useDictionaryStore();
```

**Строка 60-62:** Удалить вызов loadWords()
```typescript
// ❌ БЫЛО:
if (!previewMode) {
  setNewWordsAdded(detail?.new_words_added || 0);
  await loadWords().catch(() => {});
}

// ✅ СТАЛО:
if (!previewMode) {
  setNewWordsAdded(detail?.new_words_added || 0);
  // loadWords() удален - backend уже это сделал!
}
```

**Строка 73:** Удалить из зависимостей
```typescript
// ❌ БЫЛО:
}, [id, previewMode, reset, setLesson, normalizeType, loadWords]);

// ✅ СТАЛО:
}, [id, previewMode, reset, setLesson, normalizeType]);
```

**Строка 126:** Удалить второй вызов loadWords()
```typescript
// ❌ УДАЛИТЬ эту строку:
await loadWords().catch(() => {});
```

---

## 2️⃣ Исправление: `student-next/src/components/Navbar.tsx`

### Вариант A: Оставить только счетчик (РЕКОМЕНДУЕТСЯ)

**Строка 5:** Удалить импорт
```typescript
// ❌ УДАЛИТЬ эту строку:
import { useDictionaryStore } from "@/store/dictionaryStore";
```

**Строка 19:** Удалить destracturing
```typescript
// ❌ БЫЛО:
const { words, loadWords } = useDictionaryStore();

// ✅ СТАЛО:
const { words } = useDictionaryStore();
```

**Строка 23-30:** Удалить useEffect
```typescript
// ❌ УДАЛИТЬ весь этот блок:
useEffect(() => {
  setMounted(true);
}, []);

useEffect(() => {
  if (token) {
    loadWords().catch(() => {});
  }
}, [token, loadWords]);
```

**✅ НОВЫЙ КОД:**
```typescript
useEffect(() => {
  setMounted(true);
}, []);

// loadWords() useEffect удален!
```

---

## 3️⃣ Исправление: `student-next/src/lib/useDictionaryWords.ts`

### Полная переделка (ПЕРЕПИСАТЬ ВЕСЬ ФАЙЛ)

```typescript
import { useEffect, useMemo, useState } from "react";
import { dictionaryApi, DictionaryWord } from "@/lib/api/dictionary";
import { resolveMediaUrl } from "./media";

export type DictionaryWordView = { 
  id: number | string; 
  wordKz: string; 
  translationRu: string; 
  exampleRu?: string; 
  audioUrl?: string 
};

export const useDictionaryWords = () => {
  const [words, setWords] = useState<DictionaryWord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await dictionaryApi.getDictionaryWords();
        setWords(data);
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Failed to load dictionary");
        console.error("Failed to load dictionary words:", err);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []); // ← ВАЖНО: пустой массив - загружать ОДИН РАЗ!

  const list: DictionaryWordView[] = useMemo(() => {
    return words.map((w) => ({
      id: w.id,
      wordKz: w.word || "",
      translationRu: w.translation || "",
      exampleRu: (w as any).example_sentence || (w as any).example || "",
      audioUrl: resolveMediaUrl((w as any).audio_path || w.audio_url || undefined),
    }));
  }, [words]);

  return { words: list, loading, error };
};

export const playDictionaryAudio = (word: DictionaryWordView | undefined) => {
  if (!word) return;
  if (word.audioUrl) {
    new Audio(word.audioUrl).play();
  }
};
```

---

## 4️⃣ Исправление: `student-next/src/components/DictionaryPractice.tsx`

### Исправить useEffect (строки 15-19)

```typescript
// ❌ БЫЛО:
useEffect(() => {
  if (!words.length) {
    loadWords();
  }
}, [loadWords, words.length]);

// ✅ СТАЛО:
const [loaded, setLoaded] = useState(false);

useEffect(() => {
  if (!loaded && words.length === 0) {
    loadWords().then(() => setLoaded(true));
  }
}, []); // ← Пустой массив - загружать только один раз при монтировании!
```

**Полный контекст изменения:**
```typescript
export default function DictionaryPractice() {
  const { words, loadWords, getNextWordIndex, setCurrentIndex, currentIndex, markSuccess, markFail } = useDictionaryStore();
  const [phase, setPhase] = useState<Phase>("choose");
  const [selected, setSelected] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [pronunciationScore, setPronunciationScore] = useState<number | null>(null);
  const [loaded, setLoaded] = useState(false); // ← ДОБАВИТЬ

  useEffect(() => {
    if (!loaded && words.length === 0) {
      loadWords().then(() => setLoaded(true));
    }
  }, []); // ← ИЗМЕНИТЬ: пустой массив

  const word = words[currentIndex];
  // ... остальной код неизменен
```

---

## 5️⃣ Исправление: `student-next/src/pages/profile/index.tsx`

### Вариант A: Получить wordOfWeek отдельным запросом (РЕКОМЕНДУЕТСЯ)

**Строка 31:** Изменить деструктуризацию
```typescript
// ❌ БЫЛО:
const { words, loadWords, markSuccess } = useDictionaryStore();

// ✅ СТАЛО:
const { words, markSuccess } = useDictionaryStore(); // Удалить loadWords!
```

**Строка 69-70:** Заменить весь useEffect
```typescript
// ❌ БЫЛО:
useEffect(() => {
  if (!token) return;
  loadWords().catch(() => {});
}, [token, loadWords]);

// ✅ СТАЛО:
useEffect(() => {
  if (!token) return;
  
  const fetchWordOfWeek = async () => {
    try {
      const wordData = await dictionaryApi.getWordOfWeek?.();
      if (wordData) {
        setWordOfWeek(wordData);
      }
    } catch (err) {
      console.warn("Failed to fetch word of week:", err);
      // Не критично, если wordOfWeek не загрузился
    }
  };

  fetchWordOfWeek();
}, [token]);
```

**Важно:** Убедиться, что backend API имеет endpoint `/api/dictionary/word-of-week` или аналогичный

---

## 6️⃣ Backend: Исправление логирования

### Файл: `backend/app/services/vocabulary_service.py`

**Найти и заменить все вызовы logger.info() с dict параметрами:**

```python
# ❌ БЫЛО:
logger.info("VOCAB_SYNC_START", user_id=user_id, lesson_id=lesson.id)

# ✅ СТАЛО:
logger.info(f"VOCAB_SYNC_START: user_id={user_id}, lesson_id={lesson.id}")
```

**Пример контекста:**
```python
def sync_lesson_vocabulary(user_id: int, lesson: LessonDetail) -> int:
    """Синхронизирует словарь пользователя со словами из урока."""
    logger.info(f"VOCAB_SYNC_START: user_id={user_id}, lesson_id={lesson.id}")
    
    words_added = 0
    try:
        # ... основной код
        logger.info(f"VOCAB_SYNC_SUCCESS: user_id={user_id}, words_added={words_added}")
    except Exception as e:
        logger.error(f"VOCAB_SYNC_ERROR: user_id={user_id}, error={str(e)}")
        raise
```

---

## 7️⃣ Backend: Убедиться, что preview не синкирует

### Файл: `backend/app/api/routes/lessons.py`

**Проверить функцию `lesson_detail`:**

```python
@router.get("/lessons/{lesson_id}")
async def lesson_detail(
    lesson_id: int,
    preview: bool = False,  # ← Смотреть, есть ли этот параметр
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    detail = LessonDetail.from_orm(lesson)

    # ✅ ПРАВИЛЬНО: Только если НЕ preview!
    if not preview:  # ← ЭТА ПРОВЕРКА ДОЛЖНА БЫТЬ!
        try:
            from app.services.vocabulary_service import sync_lesson_vocabulary
            new_words_added = sync_lesson_vocabulary(current_user.id, detail)
            detail.new_words_added = new_words_added
        except Exception as e:
            logger.warning(f"Failed to sync vocabulary: {e}")
            detail.new_words_added = 0

    return detail
```

---

## 8️⃣ Добавить обработку ошибок

### Везде, где было `.catch(() => {})`

**ДО:**
```typescript
loadWords().catch(() => {});
```

**ПОСЛЕ:**
```typescript
loadWords().catch((err) => {
  console.error("Failed to load dictionary words:", err);
  // Опционально: показать уведомление пользователю
});
```

**Или с уведомлением:**
```typescript
try {
  await loadWords();
} catch (err) {
  console.error("Failed to load dictionary words:", err);
  // Показать toast или notification
  showError("Не удалось загрузить словарь");
}
```

---

## ✅ ЧЕКЛИСТ ПРИМЕНЕНИЯ

**Файлы для исправления:**
- [ ] `student-next/src/pages/lesson/[id].tsx` (4 удаления)
- [ ] `student-next/src/components/Navbar.tsx` (3 удаления)
- [ ] `student-next/src/lib/useDictionaryWords.ts` (переписать весь файл)
- [ ] `student-next/src/components/DictionaryPractice.tsx` (1 useEffect)
- [ ] `student-next/src/pages/profile/index.tsx` (1 useEffect)
- [ ] `backend/app/services/vocabulary_service.py` (логирование)
- [ ] `backend/app/api/routes/lessons.py` (проверить preview)

**Порядок применения:**
1. Backend исправления (безопасно, не ломает frontend)
2. lesson/[id].tsx (критично)
3. Navbar.tsx (критично)
4. useDictionaryWords.ts (критично)
5. DictionaryPractice.tsx (важно)
6. profile/index.tsx (важно)

**После каждого файла:**
- [ ] Проверить TypeScript ошибки
- [ ] Проверить console в браузере
- [ ] Запустить тесты если есть

---

## 🧪 ТЕСТИРОВАНИЕ ПОСЛЕ ИСПРАВЛЕНИЙ

```bash
# 1. Перестроить frontend (если были изменения)
docker-compose build --no-cache student-next

# 2. Перезапустить backend
docker-compose restart backend

# 3. Перезапустить frontend
docker-compose restart student-next

# 4. Проверить логи
docker-compose logs -f backend
docker-compose logs -f student-next
```

**Проверить в браузере:**
1. Открыть урок → смотреть Network tab, должно быть 1 запрос к backend /api/lessons/{id}
2. Открыть /dictionary → должно быть 1 запрос GET /api/dictionary
3. Открыть 2 урока подряд → должно быть 2 запроса (по одному на урок)
4. Не должно быть ошибок в console

---

