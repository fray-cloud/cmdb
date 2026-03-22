"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import type { ASN } from "@cmdb/shared";
import { asnApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";

const columns: ColumnDef<ASN>[] = [
  { accessorKey: "asn", header: "ASN" },
  { accessorKey: "rir_id", header: "RIR" },
  { accessorKey: "tenant_id", header: "Tenant" },
  { accessorKey: "description", header: "Description" },
];

export default function ASNsPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["asns", offset, limit],
    queryFn: () => asnApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">ASNs</h1>
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
