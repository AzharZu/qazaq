import { CrudPage } from "../components/crud/CrudPage";
import { modulesApi } from "../api/entities";
import { Module } from "../types";

export default function ModulesPage() {
  return (
    <CrudPage<Module>
      title="Modules"
      api={modulesApi}
      columns={[
        { key: "id", header: "ID" },
        { key: "course_id", header: "Course ID" },
        { key: "name", header: "Name" },
        { key: "order", header: "Order" },
      ]}
      fields={[
        { name: "course_id", label: "Course ID", type: "number" },
        { name: "name", label: "Name" },
        { name: "order", label: "Order", type: "number" },
        { name: "description", label: "Description", type: "textarea" },
      ]}
    />
  );
}
