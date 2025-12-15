import client from "./client";
import { Course } from "@/types/course";
import { Module } from "@/types/module";
import { LessonSummary } from "@/types/lesson";

type CoursesResponse = {
  courses: Course[];
};

export const coursesApi = {
  async list(): Promise<Course[]> {
    const { data } = await client.get<CoursesResponse>("/courses");
    return data.courses || [];
  },

  async get(idOrSlug: number | string): Promise<Course> {
    const { data } = await client.get<Course>(`/courses/${idOrSlug}`);
    return data;
  },

  async modules(courseId: number | string): Promise<Module[]> {
    const course = await coursesApi.get(courseId);
    return course.modules || [];
  },

  async lessonsForModule(moduleId: number | string): Promise<{ lessons: LessonSummary[]; progress_map: Record<number, string> }> {
    const { data } = await client.get<{ lessons: LessonSummary[]; progress_map: Record<number, string> }>(`/modules/${moduleId}/lessons`);
    return data;
  },
};

export default coursesApi;
