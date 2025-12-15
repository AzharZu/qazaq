import { LessonSummary } from "./lesson";

export interface Module {
  id: number;
  course_id: number;
  name: string;
  order: number;
  description?: string | null;
  lessons?: LessonSummary[];
  progress_map?: Record<number, string>;
}
