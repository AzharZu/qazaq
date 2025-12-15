import { useEffect, useState } from "react";
import { placementApi } from "../api/entities";
import { PlacementQuestion } from "../types";
import { DataTable } from "../components/table/DataTable";
import { Button } from "../components/ui/button";
import { Modal } from "../components/ui/modal";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { useToast } from "../components/ui/use-toast";
import { ConfirmModal } from "../components/ui/confirm-modal";

export default function PlacementPage() {
  const [data, setData] = useState<PlacementQuestion[]>([]);
  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState<{ open: boolean; id?: number }>({ open: false });
  const [form, setForm] = useState<Partial<PlacementQuestion>>({});
  const [editing, setEditing] = useState<number | null>(null);
  const { toast } = useToast();

  const refresh = async () => {
    try {
      const rows = await placementApi.list();
      setData(rows);
    } catch (err: any) {
      toast({ title: "Load failed", description: err?.message || "Error", variant: "destructive" });
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const submit = async () => {
    try {
      const payload = { ...form, answers: typeof form.answers === "string" ? safeParse(form.answers) : form.answers };
      if (editing) {
        await placementApi.update(editing, payload);
      } else {
        await placementApi.create(payload);
      }
      toast({ title: "Saved" });
      setOpen(false);
      refresh();
    } catch (err: any) {
      toast({ title: "Save failed", description: err?.message || "Error", variant: "destructive" });
    }
  };

  const remove = async () => {
    if (!confirm.id) return;
    try {
      await placementApi.remove(confirm.id);
      toast({ title: "Deleted" });
      setConfirm({ open: false });
      refresh();
    } catch (err: any) {
      toast({ title: "Delete failed", description: err?.message || "Error", variant: "destructive" });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Placement Questions</h1>
          <p className="text-sm text-gray-500">Manage placement test items</p>
        </div>
        <Button
          onClick={() => {
            setForm({});
            setEditing(null);
            setOpen(true);
          }}
        >
          Create
        </Button>
      </div>

      <DataTable
        data={data}
        columns={[
          { key: "id", header: "ID" },
          { key: "level", header: "Level" },
          { key: "question", header: "Question" },
          { key: "answers", header: "Answers", render: (row) => JSON.stringify(row.answers) },
        ]}
        onEdit={(row) => {
          setEditing(row.id);
          setForm(row);
          setOpen(true);
        }}
        onDelete={(row) => setConfirm({ open: true, id: row.id as number })}
      />

      <Modal title={editing ? "Edit Question" : "Create Question"} open={open} onOpenChange={setOpen} widthClass="w-[520px]">
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Level</label>
            <Input value={form.level || ""} onChange={(e) => setForm({ ...form, level: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Question</label>
            <Textarea value={form.question || ""} onChange={(e) => setForm({ ...form, question: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Answers (JSON)</label>
            <Textarea
              value={typeof form.answers === "string" ? form.answers : JSON.stringify(form.answers || {}, null, 2)}
              onChange={(e) => setForm({ ...form, answers: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submit}>{editing ? "Save" : "Create"}</Button>
          </div>
        </div>
      </Modal>

      <ConfirmModal
        open={confirm.open}
        title="Confirm delete"
        message="Delete this question?"
        onConfirm={remove}
        onCancel={() => setConfirm({ open: false })}
      />
    </div>
  );
}

function safeParse(value: string) {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}
