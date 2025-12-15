import client from "./client";

export const progressApi = {
  async blockFinished(payload: { lesson_id: number | string; block_id: number | string; status?: string; time_spent?: number }) {
    const { data } = await client.post("/progress/block-finished", payload);
    return data;
  },
};

export default progressApi;
