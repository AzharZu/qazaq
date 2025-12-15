export interface TestQuestion {
  id?: string;
  question: string;
  options: string[];
  correct?: number;
  section?: string;
}

export interface PlacementResult {
  score: number;
  total: number;
  raw_score?: number;
  level: string;
  recommended_course?: {
    id: number;
    slug: string;
    name: string;
    description: string;
    audience?: string;
  } | null;
}
