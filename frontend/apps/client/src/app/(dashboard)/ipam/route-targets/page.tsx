"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import type { RouteTarget } from "@cmdb/shared";
import { routeTargetApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";

const columns: ColumnDef<RouteTarget>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "tenant_id", header: "Tenant" },
  { accessorKey: "description", header: "Description" },
];

export default function RouteTargetsPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["route-targets", offset, limit],
    queryFn: () => routeTargetApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Route Targets</h1>
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
