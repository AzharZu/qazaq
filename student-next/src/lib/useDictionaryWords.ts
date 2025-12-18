import { useEffect, useMemo, useState } from "react";
import { dictionaryApi, DictionaryWord } from "@/lib/api/dictionary";
import { resolveMediaUrl } from "./media";

export type DictionaryWordView = { id: number | string; wordKz: string; translationRu: string; exampleRu?: string; audioUrl?: string };

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
  }, []);

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
    return;
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    const u = new SpeechSynthesisUtterance(word.wordKz);
    u.lang = "kk-KZ";
    window.speechSynthesis.speak(u);
  }
};
