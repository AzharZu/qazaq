import api from "./api";

export async function markBlockDone(lesson_id: number, block_index: number) {
  return api.post("/progress/block", { lesson_id, block_index, status: "done" });
}

export async function markLessonDone(lesson_id: number) {
  return api.post("/progress/lesson/done", { lesson_id });
}

export async function addXp(amount: number) {
  return api.post("/progress/xp", { amount });
}
