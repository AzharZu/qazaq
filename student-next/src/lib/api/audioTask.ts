import { mockAudioTaskCheck } from "@/lib/mockAssessments";

export const audioTaskApi = {
  async submit(block_id: number | string, payload: { answer?: string; selected_option?: number | string } = {}) {
    // Always return stubbed success; backend is bypassed for demo stability
    return mockAudioTaskCheck();
  },
};

export default audioTaskApi;
