import TheoryBlock from "./TheoryBlock";
import VideoBlock from "./VideoBlock";
import ImageBlock from "./ImageBlock";
import AudioBlock from "./AudioBlock";
import FlashcardsBlock from "./FlashcardsBlock";
import QuizBlock from "./QuizBlock";
import LessonTestBlock from "./LessonTestBlock";
import { LessonBlock } from "@/types/lesson";

export default function LessonRenderer({ blocks }: { blocks: LessonBlock[] }) {
  return (
    <div className="space-y-4">
      {blocks.map((block, idx) => {
        const blockType = (block.block_type || block.type || "").toLowerCase();
        const content = (block as any).content || block.payload || block;

        switch (blockType) {
          case "theory": {
            const title = content?.title || block.title || "";
            const text =
              typeof content?.rich_text === "string"
                ? content.rich_text
                : typeof content?.text === "string"
                  ? content.text
                  : typeof block.content === "string"
                    ? (block.content as string)
                    : "";
            return <TheoryBlock key={idx} title={title} content={text} />;
          }
          case "video":
            return <VideoBlock key={idx} url={content?.video_url || block.url || block.video_url || ""} />;
          case "image":
            return <ImageBlock key={idx} url={content?.image_url || block.image_url || ""} caption={content?.explanation || block.title} />;
          case "audio":
            return (
              <AudioBlock
                key={idx}
                url={content?.audio_path || content?.audio_url || block.audio_path || block.audio_url || ""}
                transcript={content?.transcript || content?.translation}
              />
            );
          case "flashcards":
            return <FlashcardsBlock key={idx} cards={content?.cards || block.cards || []} />;
          case "lesson_test":
            return <LessonTestBlock key={idx} questions={content?.questions || []} />;
          case "quiz":
          case "theory_quiz":
            return (
              <QuizBlock
                key={idx}
                quiz={{
                  question: content?.question || block.question || "",
                  choices: content?.options || content?.choices || block.choices || [],
                  answer: content?.correct_answer ?? content?.answer ?? block.answer ?? 0,
                }}
              />
            );
          default:
            return (
              <div key={idx} className="rounded-md border border-dashed border-slate-300 bg-white p-3 text-sm text-slate-600">
                Неизвестный блок: {blockType || "?"}
              </div>
            );
        }
      })}
    </div>
  );
}
