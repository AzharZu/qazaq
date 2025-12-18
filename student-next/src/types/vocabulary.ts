export interface VocabularyWord {
  id: number;
  word: string;
  translation: string;
  audio_path?: string | null;
  audio_url?: string | null;
  example_sentence?: string;
  image_url?: string | null;
  learned?: boolean;
  status?: "new" | "learning" | "learned" | string;
  source_lesson_id?: number | null;
  source_block_id?: number | null;
  progress?: {
    success: number;
    fails: number;
    last_review?: string | null;
  };
}
