import { CrudPage } from "../components/crud/CrudPage";
import { blocksApi } from "../api/entities";
import { Block } from "../types";

export default function BlocksPage() {
  const api = {
    list: blocksApi.list,
    create: async (payload: Partial<Block>) => {
      const content = payload.content;
      const parsed = typeof content === "string" ? safeParseJson(content) : content;
      return blocksApi.create({ ...payload, content: parsed });
    },
    update: async (id: number | string, payload: Partial<Block>) => {
      const content = payload.content;
      const parsed = typeof content === "string" ? safeParseJson(content) : content;
      return blocksApi.update(id, { ...payload, content: parsed });
    },
    remove: blocksApi.remove,
  };

  return (
    <CrudPage<Block>
      title="Blocks"
      api={api}
      columns={[
        { key: "id", header: "ID" },
        { key: "lesson_id", header: "Lesson ID" },
        { key: "type", header: "Type" },
        { key: "order", header: "Order" },
        { key: "content", header: "Content", render: (row) => JSON.stringify(row.content) },
      ]}
      fields={[
        { name: "lesson_id", label: "Lesson ID", type: "number" },
        { name: "type", label: "Type" },
        { name: "order", label: "Order", type: "number" },
        { name: "content", label: "Content (JSON)", type: "textarea" },
      ]}
    />
  );
}

function safeParseJson(value: any) {
  if (!value) return {};
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}
