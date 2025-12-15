import api from "@/lib/api";
import { PlacementResult, TestQuestion } from "@/types/test";

type PlacementStep = {
  question?: TestQuestion | null;
  index?: number;
  total?: number;
  done?: boolean;
  result?: PlacementResult;
};

export const TestService = {
  async start(): Promise<PlacementStep> {
    const { data } = await api.post("/placement/start");
    return data;
  },

  async next(): Promise<PlacementStep> {
    const { data } = await api.get("/placement/next");
    return data;
  },

  async answer(answer: number): Promise<PlacementStep> {
    const { data } = await api.post("/placement/answer", { answer });
    return data;
  },

  async result(): Promise<PlacementResult> {
    const { data } = await api.get("/placement/result");
    return data;
  },
};
