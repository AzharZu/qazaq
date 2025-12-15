import { Module } from "./module";
import { LessonSummary } from "./lesson";

export interface Course {
  id: number;
  slug: string;
  name: string;
  description: string;
  audience?: string;
  modules?: Module[];
  progress_percent?: number;
  next_lesson?: LessonSummary | null;
  progress_map?: Record<number | string, string>;
}

export interface CourseListResponse {
  courses: Course[];
}
