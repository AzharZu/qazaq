import api from "@/lib/api";
import { Course, CourseListResponse } from "@/types/course";

export const CourseService = {
  async list(): Promise<CourseListResponse> {
    const { data } = await api.get("/courses");
    return data;
  },

  async get(courseId: number | string): Promise<Course> {
    const { data } = await api.get(`/courses/${courseId}`);
    return data;
  },
};
