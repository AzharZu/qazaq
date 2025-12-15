import { CrudPage } from "../components/crud/CrudPage";
import { vocabularyApi } from "../api/entities";
import { VocabularyEntry } from "../types";

export default function VocabularyPage() {
  return (
    <CrudPage<VocabularyEntry>
      title="Vocabulary"
      api={vocabularyApi}
      columns={[
        { key: "id", header: "ID" },
        { key: "word", header: "Word" },
        { key: "translation", header: "Translation" },
        { key: "audio_url", header: "Audio URL" },
      ]}
      fields={[
        { name: "word", label: "Word" },
        { name: "translation", label: "Translation" },
        { name: "audio_url", label: "Audio URL" },
      ]}
    />
  );
}
