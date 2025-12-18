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
  mode?: string;
};

export type TextCheckIssue = {
  id: string;
  type: "grammar" | "lexicon" | "spelling" | "punctuation" | string;
  title: string;
  explanation: string;
  before: string;
  after: string;
  start: number;
  end: number;
  severity: "low" | "medium" | "high" | string;
};

export type TextCheckResponse = {
  ok: boolean;
  request_id?: string;
  language: "ru" | "kk";
  level: string;
  scores: {
    grammar: number;
    lexicon: number;
    spelling: number;
    punctuation: number;
    overall: number;
  };
  before_text: string;
  after_text: string;
  highlighted_html: string;
  issues: TextCheckIssue[];
  recommendations: string[];
  suggested_text: string;
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
