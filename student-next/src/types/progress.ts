import { LessonSummary } from "./lesson";

export interface ProgressResponse {
  course_id: number | null;
  course_slug?: string | null;
  course_title?: string | null;
  completed_lessons: number;
  total_lessons: number;
  percent: number;
  completed_modules: any[];
  completed_module_names: string[];
  completed_lesson_titles: string[];
  certificates: any[];
  next_lesson: LessonSummary | null;
  progress_map: Record<number, string>;
  xp_total: number;
  xp_today: number;
  streak_days: number;
  goal_today: {
    target?: number;
    completed?: boolean;
    goal_type?: string;
  };
}
