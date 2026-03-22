"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { ColumnDef } from "@tanstack/react-table";
import type { Prefix } from "@cmdb/shared";
import { prefixApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

const columns: ColumnDef<Prefix>[] = [
  { accessorKey: "network", header: "Network" },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
  },
  { accessorKey: "vrf_id", header: "VRF" },
  { accessorKey: "role", header: "Role" },
  { accessorKey: "tenant_id", header: "Tenant" },
  { accessorKey: "description", header: "Description" },
];

export default function PrefixesPage() {
  const router = useRouter();
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["prefixes", offset, limit],
    queryFn: () => prefixApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Prefixes</h1>
        <Button onClick={() => router.push("/ipam/prefixes/new")}>
          <Plus />
          New Prefix
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
        onRowClick={(row) => router.push(`/ipam/prefixes/${row.id}`)}
      />
    </div>
  );
}
