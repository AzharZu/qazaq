import { CrudPage } from "../components/crud/CrudPage";
import { lessonsApi } from "../api/entities";
import { Lesson } from "../types";

export default function LessonsPage() {
  return (
    <CrudPage<Lesson>
      title="Lessons"
      api={lessonsApi}
      columns={[
        { key: "id", header: "ID" },
        { key: "module_id", header: "Module ID" },
        { key: "title", header: "Title" },
        { key: "order", header: "Order" },
      ]}
      fields={[
        { name: "module_id", label: "Module ID", type: "number" },
        { name: "title", label: "Title" },
        { name: "description", label: "Description", type: "textarea" },
        { name: "order", label: "Order", type: "number" },
      ]}
    />
  );
}
