import { useEffect, useMemo } from "react";
import { useDictionaryStore } from "@/store/dictionaryStore";

export type DictionaryWordView = { id: number | string; wordKz: string; translationRu: string; exampleRu?: string; audioUrl?: string };

export const useDictionaryWords = (opts?: { lessonId?: number | string }) => {
  const { words, loadWords, loading } = useDictionaryStore();
  const lessonFilter = opts?.lessonId;

  useEffect(() => {
    loadWords(lessonFilter);
  }, [lessonFilter, loadWords]);

  const list: DictionaryWordView[] = useMemo(
    () =>
      words.map((w) => {
        const example = (w as any).example ?? (w as any).example_sentence;
        return {
          id: w.id,
          wordKz: w.word || w.translation || "",
          translationRu: w.translation || w.word || "",
          exampleRu: example,
          audioUrl: w.audio_url || undefined,
        };
      }),
    [words]
  );

  return { words: list, loading };
};

export const playDictionaryAudio = (word: DictionaryWordView | undefined) => {
  if (!word) return;
  if (word.audioUrl) {
    new Audio(word.audioUrl).play();
    return;
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    const u = new SpeechSynthesisUtterance(word.wordKz);
    u.lang = "kk-KZ";
    window.speechSynthesis.speak(u);
  }
};
