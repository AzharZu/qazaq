import client from "./client";

export type PronunciationResult = {
  score: number;
  status: "excellent" | "good" | "bad";
  audio_url: string;
  word_id: number;
  feedback?: string;
};

export async function checkPronunciation(wordId: number, audioBlob: Blob): Promise<PronunciationResult> {
  const formData = new FormData();
  formData.append("word_id", wordId.toString());
  formData.append("audio", audioBlob, "audio.webm");
  const { data } = await client.post<PronunciationResult>("/pronunciation/check", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

const pronunciationApi = { checkPronunciation };
export default pronunciationApi;
