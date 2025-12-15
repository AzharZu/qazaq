import api from "@/lib/api";
import { ProgressResponse } from "@/types/progress";

export const ProgressService = {
  async overview(courseId?: number | string): Promise<ProgressResponse> {
    const url = courseId ? `/progress?course_id=${courseId}` : "/progress";
    const { data } = await api.get(url);
    return data;
  },
};
