import client from "./client";

export type AutoCheckerMistake = {
  fragment: string;
  issue: string;
  explanation: string;
  suggestion: string;
};

export type AutoCheckerHtmlResponse = {
  ai_used: boolean;
  model: string | null;
  overall_score: number;
  categories: {
    grammar: number;
    vocabulary: number;
    word_order: number;
    clarity: number;
  };
  mistakes: AutoCheckerMistake[];
  mentor_feedback: string;
  improved_version: string;
  recommendations: string[];
  error?: string;
};

const normalizeNumber = (value: unknown) => {
  const parsed = typeof value === "number" ? value : Number.parseFloat(`${value ?? 0}`);
  return Number.isFinite(parsed) ? parsed : 0;
};

const normalizeArray = (value: unknown) => {
  if (Array.isArray(value)) return value;
  if (!value) return [];
  return [value];
};

export const autocheckerApi = {
  async check(text: string): Promise<AutoCheckerHtmlResponse> {
    const { data } = await client.post<AutoCheckerHtmlResponse>("/autochecker/html", {
      text,
      language: "kazakh",
    });

    const categoriesRaw = data.categories || {};
    const mistakes = normalizeArray(data.mistakes).map((item: any) => ({
      fragment: `${item?.fragment ?? ""}`.trim(),
      issue: `${item?.issue ?? ""}`.trim(),
      explanation: `${item?.explanation ?? ""}`.trim(),
      suggestion: `${item?.suggestion ?? ""}`.trim(),
    }));

    const recommendations = normalizeArray(data.recommendations).map((item: any) =>
      `${item ?? ""}`.trim()
    );

    return {
      ai_used: Boolean(data.ai_used),
      model: data.model || null,
      overall_score: Math.min(100, Math.max(0, normalizeNumber(data.overall_score))),
      categories: {
        grammar: Math.min(100, Math.max(0, normalizeNumber(categoriesRaw.grammar))),
        vocabulary: Math.min(100, Math.max(0, normalizeNumber(categoriesRaw.vocabulary))),
        word_order: Math.min(100, Math.max(0, normalizeNumber(categoriesRaw.word_order))),
        clarity: Math.min(100, Math.max(0, normalizeNumber(categoriesRaw.clarity))),
      },
      mistakes: mistakes.filter(
        (m) => m.fragment || m.issue || m.explanation || m.suggestion
      ),
      mentor_feedback: `${data.mentor_feedback ?? ""}`.trim(),
      improved_version: `${data.improved_version ?? ""}`.trim(),
      recommendations: recommendations.filter(Boolean),
      error: data.error ? `${data.error}` : undefined,
    };
  },

  async ping() {
    const { data } = await client.get<{ status: string }>("/autochecker/ping");
    return data;
  },
};

export default autocheckerApi;
