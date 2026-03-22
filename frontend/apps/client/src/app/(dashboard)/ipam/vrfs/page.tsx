"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { ColumnDef } from "@tanstack/react-table";
import type { VRF } from "@cmdb/shared";
import { vrfApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

const columns: ColumnDef<VRF>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "rd", header: "RD" },
  {
    accessorKey: "import_targets",
    header: "Import Targets",
    cell: ({ row }) => row.original.import_targets.join(", ") || "-",
  },
  {
    accessorKey: "export_targets",
    header: "Export Targets",
    cell: ({ row }) => row.original.export_targets.join(", ") || "-",
  },
  { accessorKey: "tenant_id", header: "Tenant" },
  { accessorKey: "description", header: "Description" },
];

export default function VRFsPage() {
  const router = useRouter();
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["vrfs", offset, limit],
    queryFn: () => vrfApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">VRFs</h1>
        <Button onClick={() => router.push("/ipam/vrfs/new")}>
          <Plus />
          New VRF
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
        onRowClick={(row) => router.push(`/ipam/vrfs/${row.id}`)}
      />
    </div>
  );
}
