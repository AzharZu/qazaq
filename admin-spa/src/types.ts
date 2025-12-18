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
  name: string;
  order: number;
  description?: string;
  lessons?: Lesson[];
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
  | "pronunciation"
  | "free_writing";

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
  video_type?: string; // youtube, vimeo, file
  video_url?: string;
};

export type VocabularyEntry = {
  id: number;
  word: string;
  translation: string;
  audio_path?: string;
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
