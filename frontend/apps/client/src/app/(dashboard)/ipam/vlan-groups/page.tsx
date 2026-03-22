"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import type { VLANGroup } from "@cmdb/shared";
import { vlanGroupApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";

const columns: ColumnDef<VLANGroup>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "slug", header: "Slug" },
  {
    id: "vid_range",
    header: "VID Range",
    cell: ({ row }) => `${row.original.min_vid}-${row.original.max_vid}`,
  },
  { accessorKey: "tenant_id", header: "Tenant" },
];

export default function VLANGroupsPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["vlan-groups", offset, limit],
    queryFn: () => vlanGroupApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">VLAN Groups</h1>
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
