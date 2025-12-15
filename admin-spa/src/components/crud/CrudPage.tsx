import { useEffect, useCallback, useState } from "react";
import { DataTable, type Column } from "../table/DataTable";
import { Button } from "../ui/button";
import { Modal } from "../ui/modal";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { ConfirmModal } from "../ui/confirm-modal";
import { useToast } from "../ui/use-toast";

type CrudApi<T> = {
  list: () => Promise<T[]>;
  create: (payload: Partial<T>) => Promise<T>;
  update: (id: number | string, payload: Partial<T>) => Promise<T>;
  remove: (id: number | string) => Promise<void>;
};

type Field = {
  name: string;
  label: string;
  type?: "text" | "textarea" | "number";
};

type Props<T extends { id: number | string }> = {
  title: string;
  api: CrudApi<T>;
  columns: Column<T>[];
  fields: Field[];
};

export function CrudPage<T extends { id: number | string }>({ title, api, columns, fields }: Props<T>) {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [confirm, setConfirm] = useState<{ open: boolean; id?: number | string }>({ open: false });
  const [form, setForm] = useState<Record<string, any>>({});
  const [editingId, setEditingId] = useState<number | string | null>(null);
  const { toast } = useToast();

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await api.list();
      const normalized = Array.isArray(rows)
        ? rows
        : Array.isArray((rows as any)?.items)
          ? (rows as any).items
          : Array.isArray((rows as any)?.data)
            ? (rows as any).data
            : Array.isArray((rows as any)?.courses)
              ? (rows as any).courses
              : [];
      setData(normalized as T[]);
    } catch (err: any) {
      toast({ title: "Load failed", description: err?.message || "Error loading data", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [api, toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const openCreate = () => {
    setForm({});
    setEditingId(null);
    setDrawerOpen(true);
  };

  const openEdit = (row: T) => {
    setForm(row as any);
    setEditingId(row.id);
    setDrawerOpen(true);
  };

  const submit = async () => {
    try {
      if (editingId) {
        await api.update(editingId, form);
        toast({ title: "Updated" });
      } else {
        await api.create(form);
        toast({ title: "Created" });
      }
      setDrawerOpen(false);
      refresh();
    } catch (err: any) {
      toast({ title: "Save failed", description: err?.message || "Error", variant: "destructive" });
    }
  };

  const remove = async () => {
    if (!confirm.id) return;
    try {
      await api.remove(confirm.id);
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
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p className="text-sm text-gray-500">Manage {title.toLowerCase()}</p>
        </div>
        <Button onClick={openCreate}>Create</Button>
      </div>

      <DataTable data={data} columns={columns} onEdit={openEdit} onDelete={(row) => setConfirm({ open: true, id: row.id })} loading={loading} />

      <Modal title={editingId ? `Edit ${title}` : `Create ${title}`} open={drawerOpen} onOpenChange={setDrawerOpen} widthClass="w-[520px]">
        <div className="space-y-3">
          {fields.map((field) => (
            <div key={field.name}>
              <label className="mb-1 block text-sm font-medium text-gray-700">{field.label}</label>
              {field.type === "textarea" ? (
                <Textarea value={form[field.name] || ""} onChange={(e) => setForm({ ...form, [field.name]: e.target.value })} />
              ) : (
                <Input
                  type={field.type === "number" ? "number" : "text"}
                  value={form[field.name] ?? ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      [field.name]: field.type === "number" ? Number(e.target.value) : e.target.value,
                    })
                  }
                />
              )}
            </div>
          ))}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setDrawerOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submit}>{editingId ? "Save" : "Create"}</Button>
          </div>
        </div>
      </Modal>

      <ConfirmModal
        open={confirm.open}
        title="Confirm delete"
        message="Are you sure you want to delete this item?"
        onConfirm={remove}
        onCancel={() => setConfirm({ open: false })}
      />
    </div>
  );
}
