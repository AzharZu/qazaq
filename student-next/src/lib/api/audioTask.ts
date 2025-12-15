import client from "./client";

export const audioTaskApi = {
  async submit(block_id: number | string, payload: { answer?: string; selected_option?: number | string } = {}) {
    const { data } = await client.post("/audio-task/submit", { block_id, ...payload });
    return data as { correct: boolean; feedback?: string; expected?: string };
  },
};

export default audioTaskApi;
