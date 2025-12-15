import { useEffect, useState } from "react";
import { usersApi } from "../api/entities";
import { UserRow } from "../types";
import { DataTable } from "../components/table/DataTable";
import { Card, CardContent, CardTitle } from "../components/ui/card";
import { useToast } from "../components/ui/use-toast";

export default function UsersPage() {
  const [data, setData] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const rows = await usersApi.list();
        setData(rows);
      } catch (err: any) {
        toast({ title: "Load failed", description: err?.message || "Error", variant: "destructive" });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [toast]);

  return (
    <Card>
      <CardTitle>Users</CardTitle>
      <CardContent className="mt-3">
        <DataTable
          data={data}
          loading={loading}
          columns={[
            { key: "id", header: "ID" },
            { key: "email", header: "Email" },
            { key: "role", header: "Role" },
            { key: "level", header: "Level" },
          ]}
        />
      </CardContent>
    </Card>
  );
}
