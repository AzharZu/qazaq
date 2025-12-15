export interface LessonSummary {
  id: number;
  module_id: number;
  title: string;
  order: number;
  status: string;
  description?: string | null;
  difficulty?: string | null;
  estimated_time?: number | null;
  language?: string | null;
  blocks_order?: number[] | null;
}

export interface LessonBlock {
  id?: number;
  order?: number;
  block_type?: string;
  blockType?: string;
  type?: string;
  title?: string;
  word?: string;
  content?: string;
  data?: any;
  payload?: any;
  url?: string;
  video_url?: string;
  image_url?: string;
  audio_url?: string;
  markdown?: string;
  word_id?: number;
  word_ids?: number[];
  cards?: Flashcard[];
  items?: Flashcard[];
  question?: string;
  choices?: string[];
  options?: string[];
  answer?: number;
  transcript?: string;
  translation?: string;
  expected_pronunciation?: string;
  phrase?: string;
  sample_audio_url?: string;
}

export interface Flashcard {
  id?: number;
  front?: string;
  back?: string;
  word?: string;
  translation: string;
  image_url?: string | null;
  audio_url?: string | null;
  example_sentence?: string;
}

export interface Quiz {
  id?: number;
  question: string;
  options: string[];
  correct_option: number;
  explanation?: string | null;
  order?: number;
}

export type BlockType =
  | "video"
  | "theory"
  | "audio_theory"
  | "image"
  | "audio"
  | "flashcards"
  | "pronunciation"
  | "quiz"
  | "theory_quiz"
  | "lesson_test"
  | "audio_task";

export type TheoryContent = {
  title?: string;
  markdown?: string;
  rich_text?: string;
  video_url?: string;
  thumbnail_url?: string;
};

export type FlashcardsContent = {
  cards: Flashcard[];
};

export type PronunciationItem = {
  id?: number | string;
  word?: string;
  translation?: string;
  example?: string;
  image_url?: string | null;
  audio_url?: string | null;
};

export type PronunciationContent = {
  items: PronunciationItem[];
  sample_audio_url?: string;
  expected_pronunciation?: string;
  phrase?: string;
};

export type TaskQuestion = {
  question: string;
  type: "audio" | "audio_repeat" | "single" | "single_choice" | "fill-in" | "open";
  options?: string[];
  audio_url?: string;
  placeholder?: string;
};

export type TasksContent = {
  questions: TaskQuestion[];
};

export interface LessonDetail {
  lesson: LessonSummary & {
    module: {
      id: number;
      order?: number;
      course?: { slug?: string };
    };
    blocks?: LessonBlock[];
    flashcards?: Flashcard[];
    quizzes?: Quiz[];
  };
  blocks: LessonBlock[];
  flashcards: Flashcard[];
  quizzes: Quiz[];
  progress_status: string;
  score?: number | null;
  time_spent?: number | null;
  course_progress: number;
  module_progress: number;
  progress_map: Record<number, string>;
  navigation: {
    prev_lesson_id?: number | null;
    next_lesson_id?: number | null;
  };
  new_words_added?: number;
}
