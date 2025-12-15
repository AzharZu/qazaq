export type Course = {
  id: number;
  slug: string;
  name: string;
  description?: string;
  audience?: string;
};

export type Module = {
  id: number;
  course_id: number;
  title: string;
  order: number;
};

export type BlockType =
  | "video"
  | "theory"
  | "audio_theory"
  | "theory_quiz"
  | "quiz"
  | "audio_task"
  | "lesson_test"
  | "image"
  | "audio"
  | "flashcards"
  | "pronunciation";

export type LessonBlock = {
  id: number;
  lesson_id?: number;
  type: BlockType;
  content: Record<string, any>;
  data?: Record<string, any>;
  order: number;
};

export type Lesson = {
  id: number;
  module_id: number;
  title: string;
  description?: string;
  order: number;
  status?: string;
  difficulty?: string;
  estimated_time?: number;
  language?: string;
  blocks_order?: number[];
  blocks?: LessonBlock[];
};

export type VocabularyEntry = {
  id: number;
  word: string;
  translation: string;
  audio_url?: string;
};

export type PlacementQuestion = {
  id: number;
  question: string;
  answers: any;
  level: string;
};

export type UserRow = {
  id: number;
  email: string;
  role?: string;
  level?: string | null;
};
