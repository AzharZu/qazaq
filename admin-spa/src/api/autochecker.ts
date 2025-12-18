import { api } from "./client";

export type FreeWritingPayload = {
  prompt: string;
  student_answer: string;
  rubric?: string;
  language?: string;
};

export type FreeWritingResult = {
  ok: boolean;
  score?: number | null;
  level?: string | null;
  feedback?: string | null;
  corrections?: string[];
  model?: string | null;
  error?: string;
  details?: any;
  request_id?: string;
};

export type TextCheckPayload = {
  text: string;
  language: "ru" | "kk";
  mode?: string;
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
  issues: Array<{
    id: string;
    type: string;
    title: string;
    explanation: string;
    before: string;
    after: string;
    start: number;
    end: number;
    severity: string;
  }>;
  recommendations: string[];
  suggested_text: string;
  error?: string;
  details?: any;
};

export const autocheckerApi = {
  async health() {
    const { data } = await api.get<{ ok: boolean; provider: string; key_present: boolean; error?: string; details?: any; request_id?: string }>(
      "autochecker/health",
    );
    return data;
  },

  async checkFreeWriting(payload: FreeWritingPayload): Promise<FreeWritingResult> {
    const { data } = await api.post<FreeWritingResult>("autochecker/free-writing/check", payload);
    return data;
  },

  async textCheck(payload: TextCheckPayload): Promise<TextCheckResponse> {
    const { data } = await api.post<TextCheckResponse>("autochecker/text-check", payload);
    return data;
  },
};

export default autocheckerApi;
