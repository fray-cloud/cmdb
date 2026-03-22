"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { ColumnDef } from "@tanstack/react-table";
import type { VLAN } from "@cmdb/shared";
import { vlanApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

const columns: ColumnDef<VLAN>[] = [
  { accessorKey: "vid", header: "VID" },
  { accessorKey: "name", header: "Name" },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
  },
  { accessorKey: "group_id", header: "Group" },
  { accessorKey: "role", header: "Role" },
  { accessorKey: "tenant_id", header: "Tenant" },
  { accessorKey: "description", header: "Description" },
];

export default function VLANsPage() {
  const router = useRouter();
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["vlans", offset, limit],
    queryFn: () => vlanApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">VLANs</h1>
        <Button onClick={() => router.push("/ipam/vlans/new")}>
          <Plus />
          New VLAN
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        pagination={
          data ? { offset: data.offset, limit: data.limit, total: data.total } : undefined
        }
        onPaginationChange={setOffset}
        onRowClick={(row) => router.push(`/ipam/vlans/${row.id}`)}
      />
    </div>
  );
}
