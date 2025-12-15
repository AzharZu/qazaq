import { CrudPage } from "../components/crud/CrudPage";
import { coursesApi } from "../api/entities";
import { Course } from "../types";

export default function CoursesPage() {
  return (
    <CrudPage<Course>
      title="Courses"
      api={coursesApi}
      columns={[
        { key: "id", header: "ID" },
        { key: "name", header: "Name" },
        { key: "slug", header: "Slug" },
        { key: "description", header: "Description" },
      ]}
      fields={[
        { name: "name", label: "Name" },
        { name: "slug", label: "Slug" },
        { name: "description", label: "Description", type: "textarea" },
        { name: "audience", label: "Audience" },
      ]}
    />
  );
}
