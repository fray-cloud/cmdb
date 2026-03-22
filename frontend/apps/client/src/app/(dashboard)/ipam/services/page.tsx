"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import type { Service } from "@cmdb/shared";
import { serviceApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";

const columns: ColumnDef<Service>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "protocol", header: "Protocol" },
  {
    accessorKey: "ports",
    header: "Ports",
    cell: ({ row }) => row.original.ports.join(", "),
  },
  { accessorKey: "description", header: "Description" },
];

export default function ServicesPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["services", offset, limit],
    queryFn: () => serviceApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Services</h1>
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
