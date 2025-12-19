import client from "./client";
import { PlacementResult, TestQuestion, parsePlacementResult } from "@/types/test";

type QuestionsResponse = {
  questions: TestQuestion[];
  total: number;
};

type AnswerPayload = {
  question_id: string;
  selected_option: number;
};

export const testApi = {
  async fetchQuestions(limit = 20): Promise<QuestionsResponse> {
    const { data } = await client.get<QuestionsResponse>(`/placement/questions?limit=${limit}`);
    return data;
  },

  async submitAnswer(answer: AnswerPayload) {
    const { data } = await client.post("/placement/answer", answer);
    return data;
  },

  async finish(answers: AnswerPayload[], limit?: number): Promise<PlacementResult> {
    const payload = { answers, limit: limit || answers.length || 20 };
    const { data } = await client.post<PlacementResult>("/placement/finish", payload);
    const parsed = parsePlacementResult(data);
    if (!parsed) {
      throw new Error("Invalid placement result payload");
    }
    return parsed;
  },

  async result(): Promise<PlacementResult> {
    const { data } = await client.get<PlacementResult>("/placement/result");
    const parsed = parsePlacementResult(data);
    if (!parsed) {
      throw new Error("Invalid placement result payload");
    }
    return parsed;
  },
};

export default testApi;
