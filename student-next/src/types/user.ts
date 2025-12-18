export interface User {
  id: number;
  email: string;
  role?: string;
  age?: number;
  target?: string;
  daily_minutes?: number;
  level?: string | null;
  full_name?: string | null;
  recommended_course?: string | null;
  completed_lessons_count?: number | null;
  name?: string;
}
