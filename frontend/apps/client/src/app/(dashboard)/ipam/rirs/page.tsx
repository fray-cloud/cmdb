"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import type { RIR } from "@cmdb/shared";
import { rirApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";

const columns: ColumnDef<RIR>[] = [
  { accessorKey: "name", header: "Name" },
  {
    accessorKey: "is_private",
    header: "Private",
    cell: ({ row }) => (row.original.is_private ? "Yes" : "No"),
  },
  { accessorKey: "description", header: "Description" },
];

export default function RIRsPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["rirs", offset, limit],
    queryFn: () => rirApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">RIRs</h1>
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        pagination={
          data ? { offset: data.offset, limit: data.limit, total: data.total } : undefined
        }
        onPaginationChange={setOffset}
      />
    </div>
  );
}
