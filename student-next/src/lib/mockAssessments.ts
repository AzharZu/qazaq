const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const MOCK_CHECKS_ENABLED = process.env.NEXT_PUBLIC_USE_MOCK_CHECKS !== "0";

export const PRONUNCIATION_FEEDBACK =
  "Произношение в целом хорошее, но рекомендуется поработать над ударением и чёткостью отдельных звуков.";

export type MockPronunciationResult = {
  score: number;
  status: "excellent" | "good" | "bad";
  audio_url: string;
  word_id: number;
  feedback: string;
};

export type MockAudioTaskResult = {
  correct: boolean;
  feedback: string;
  expected?: string;
  score?: number;
};

export type MockFreeWritingResult = {
  ok: boolean;
  score: number;
  level: "excellent";
  feedback: string;
  corrections: string[];
  model: "stub";
};

const randomDelay = () => 600 + Math.floor(Math.random() * 500);

export async function mockPronunciationCheck(wordId?: number): Promise<MockPronunciationResult> {
  await delay(randomDelay());
  return {
    score: 0.9,
    status: "excellent",
    audio_url: "mock://audio",
    word_id: wordId ?? -1,
    feedback: PRONUNCIATION_FEEDBACK,
  };
}

export async function mockAudioTaskCheck(): Promise<MockAudioTaskResult> {
  await delay(randomDelay());
  return {
    correct: true,
    feedback: "Ответ принят",
    expected: undefined,
    score: 10,
  };
}

export async function mockFreeWritingCheck(): Promise<MockFreeWritingResult> {
  await delay(randomDelay());
  return {
    ok: true,
    score: 10,
    level: "excellent",
    feedback: "Грамматика ок. Пишите казахскими буквами, расширяйте словарный запас и используйте больше слов из урока.",
    corrections: [],
    model: "stub",
  };
}

export function computeStubLessonScore(hasPronunciation: boolean) {
  const total = 10;
  const score = hasPronunciation ? 9 : 10;
  const reason = "Проверяется автоматически нашим ИИ";
  return { score, total, reason };
}
