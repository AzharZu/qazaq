import client from "./client";
import { mockPronunciationCheck } from "@/lib/mockAssessments";

export type PronunciationResult = {
  score: number;
  status: "excellent" | "good" | "ok" | "bad";
  audio_url: string;
  word_id: number;
  feedback?: string;
  tips?: string[];
};

export async function checkPronunciation(phrase: string, language?: string): Promise<PronunciationResult> {
  try {
    const { data } = await client.post("/pronunciation/mock-check", {
      phrase,
      language: (language || "kk").toLowerCase(),
    });
    return {
      score: data?.score ?? 9,
      status: (data?.status as PronunciationResult["status"]) || "excellent",
      audio_url: data?.audio_url || "",
      word_id: data?.word_id || -1,
      feedback: data?.feedback,
      tips: data?.tips || [],
    };
  } catch (_err) {
    return mockPronunciationCheck(undefined);
  }
}

const pronunciationApi = { checkPronunciation };
export default pronunciationApi;
