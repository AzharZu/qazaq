export interface TestQuestion {
  id?: string;
  question?: string;
  prompt?: string;
  text?: string;
  title?: string;
  label?: string;
  name?: string;
  body?: string;
  content?: string;
  description?: string;
  options: string[];
  correct?: number;
  correct_option?: number;
  section?: string;
}

export interface RecommendedCourseInfo {
  id?: number;
  slug?: string;
  name?: string;
  description?: string;
  audience?: string;
}

export interface PlacementResult {
  score: number;
  total: number;
  raw_score?: number;
  level: string;
  recommended_course?: string | RecommendedCourseInfo | null;
  course?: RecommendedCourseInfo | null;
}
