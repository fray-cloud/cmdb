"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import type { IPRange } from "@cmdb/shared";
import { ipRangeApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";
import { StatusBadge } from "@/components/status-badge";

const columns: ColumnDef<IPRange>[] = [
  { accessorKey: "start_address", header: "Start" },
  { accessorKey: "end_address", header: "End" },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
  },
  { accessorKey: "vrf_id", header: "VRF" },
  { accessorKey: "description", header: "Description" },
];

export default function IPRangesPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["ip-ranges", offset, limit],
    queryFn: () => ipRangeApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">IP Ranges</h1>
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
