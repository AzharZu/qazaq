import client from "@/lib/api/client";

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

export type FreeWritingRequest = {
  prompt: string;
  student_answer: string;
  rubric?: string;
  language?: string;
};

export type FreeWritingResponse = {
  ok: boolean;
  score?: number | null;
  level?: "excellent" | "good" | "ok" | "weak" | string | null;
  feedback?: string | null;
  corrections?: string[];
  model?: string | null;
  error?: string;
  details?: any;
  request_id?: string;
};

export type TextCheckRequest = {
  text: string;
  language: "ru" | "kk";
  level: "A1" | "A2" | "B1";
  mode?: string;
};

export type TextCheckIssue = {
  type: "grammar" | "lexicon" | "spelling" | "punctuation" | string;
  severity: "low" | "medium" | "high" | string;
  bad_excerpt: string;
  fix: string;
  why: string;
};

export type TextCheckSummary = {
  grammar: number;
  lexicon: number;
  spelling: number;
  punctuation: number;
};

export type TextCheckResponse = {
  ok: boolean;
  request_id?: string;
  language: "ru" | "kk";
  level: "A1" | "A2" | "B1" | string;
  score: number;
  summary: TextCheckSummary;
  issues: TextCheckIssue[];
  corrected_text: string;
  original_text: string;
  warning?: string;
  error?: string;
  details?: any;
};

export const autocheckerApi = {
  async ping() {
    const { data } = await client.get("/autochecker/ping");
    return data;
  },

  async health() {
    const { data } = await client.get("/autochecker/health");
    return data;
  },

  async checkFreeWriting(payload: FreeWritingRequest): Promise<FreeWritingResponse> {
    const { data } = await client.post("/autochecker/free-writing/check", payload);
    return data as FreeWritingResponse;
  },

  async textCheck(payload: TextCheckRequest): Promise<TextCheckResponse> {
    const { data } = await client.post("/autochecker/text-check", payload);
    return data as TextCheckResponse;
  },
};

export default autocheckerApi;
