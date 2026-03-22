"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { ColumnDef } from "@tanstack/react-table";
import type { IPAddress } from "@cmdb/shared";
import { ipAddressApi } from "@cmdb/shared";
import { DataTable } from "@/components/data-table";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

const columns: ColumnDef<IPAddress>[] = [
  { accessorKey: "address", header: "Address" },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
  },
  { accessorKey: "vrf_id", header: "VRF" },
  { accessorKey: "dns_name", header: "DNS Name" },
  { accessorKey: "tenant_id", header: "Tenant" },
  { accessorKey: "description", header: "Description" },
];

export default function IPAddressesPage() {
  const router = useRouter();
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["ip-addresses", offset, limit],
    queryFn: () => ipAddressApi.list({ offset, limit }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">IP Addresses</h1>
        <Button onClick={() => router.push("/ipam/ip-addresses/new")}>
          <Plus />
          New IP Address
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
        onRowClick={(row) => router.push(`/ipam/ip-addresses/${row.id}`)}
      />
    </div>
  );
}
