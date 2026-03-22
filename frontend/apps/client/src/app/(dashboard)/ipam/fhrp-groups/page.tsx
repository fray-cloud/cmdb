"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import type { FHRPGroup } from "@cmdb/shared";
import { fhrpGroupApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";

const columns: ColumnDef<FHRPGroup>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "protocol", header: "Protocol" },
  { accessorKey: "group_id_value", header: "Group ID" },
  { accessorKey: "auth_type", header: "Auth Type" },
];

export default function FHRPGroupsPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["fhrp-groups", offset, limit],
    queryFn: () => fhrpGroupApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">FHRP Groups</h1>
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
