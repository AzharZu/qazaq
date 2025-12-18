export const resolveQuestionText = (q: any): string => {
  if (!q) return "";

  const candidates = [
    q.text,
    q.question,
    q.prompt,
    q.title,
    q.label,
    q.name,
    q.body,
    q.content,
    q.description,
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim().length) {
      return value.trim();
    }
    if (value !== undefined && value !== null && typeof value !== "object") {
      return String(value);
    }
  }

  return "";
};
