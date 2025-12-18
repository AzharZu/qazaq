import { mockFreeWritingCheck } from "@/lib/mockAssessments";

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
    // Stub perfect response without network
    return {
      ai_used: false,
      model: "stub",
      overall_score: 100,
      categories: {
        grammar: 100,
        vocabulary: 100,
        word_order: 100,
        clarity: 100,
      },
      mistakes: [],
      mentor_feedback: "Текст принят. Грамматика в норме.",
      improved_version: text,
      recommendations: [],
    };
  },

  async ping() {
    return { status: "ok (stub)" };
  },

  async health() {
    return { ok: true, provider: "stub", key_present: true, request_id: "stub" };
  },

  async checkFreeWriting(payload: FreeWritingRequest): Promise<FreeWritingResponse> {
    // Always return stubbed success; backend is bypassed for demo stability
    return mockFreeWritingCheck();
  },

  async textCheck(payload: TextCheckRequest): Promise<TextCheckResponse> {
    // Stubbed response: accept everything with perfect score
    return {
      ok: true,
      request_id: "stub",
      language: payload.language,
      level: "excellent",
      scores: {
        grammar: 100,
        lexicon: 100,
        spelling: 100,
        punctuation: 100,
        overall: 100,
      },
      before_text: payload.text,
      after_text: payload.text,
      highlighted_html: payload.text,
      issues: [],
      recommendations: [],
      suggested_text: payload.text,
    };
  },
};

export default autocheckerApi;
