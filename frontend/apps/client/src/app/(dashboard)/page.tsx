"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  prefixApi,
  ipAddressApi,
  vrfApi,
  vlanApi,
  changelogApi,
} from "@cmdb/shared";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Globe, Hash, Layers, Network } from "lucide-react";

const ACTION_STYLES: Record<string, string> = {
  created: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  updated: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  deleted: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

export default function DashboardPage() {
  const { data: prefixes, isLoading: loadingPrefixes } = useQuery({
    queryKey: ["dashboard-prefixes"],
    queryFn: () => prefixApi.list({ limit: 1, offset: 0 }),
  });

  const { data: ipAddresses, isLoading: loadingIPs } = useQuery({
    queryKey: ["dashboard-ip-addresses"],
    queryFn: () => ipAddressApi.list({ limit: 1, offset: 0 }),
  });

  const { data: vrfs, isLoading: loadingVRFs } = useQuery({
    queryKey: ["dashboard-vrfs"],
    queryFn: () => vrfApi.list({ limit: 1, offset: 0 }),
  });

  const { data: vlans, isLoading: loadingVLANs } = useQuery({
    queryKey: ["dashboard-vlans"],
    queryFn: () => vlanApi.list({ limit: 1, offset: 0 }),
  });

  const stats = [
    {
      title: "Prefixes",
      value: prefixes?.total,
      loading: loadingPrefixes,
      icon: Network,
      href: "/ipam/prefixes",
    },
    {
      title: "IP Addresses",
      value: ipAddresses?.total,
      loading: loadingIPs,
      icon: Hash,
      href: "/ipam/ip-addresses",
    },
    {
      title: "VRFs",
      value: vrfs?.total,
      loading: loadingVRFs,
      icon: Layers,
      href: "/ipam/vrfs",
    },
    {
      title: "VLANs",
      value: vlans?.total,
      loading: loadingVLANs,
      icon: Globe,
      href: "/ipam/vlans",
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">IPAM Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link key={stat.title} href={stat.href}>
            <Card className="transition-colors hover:bg-accent/50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {stat.loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <div className="text-2xl font-bold">{stat.value ?? 0}</div>
                )}
                <p className="text-xs text-muted-foreground">Total count</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <RecentChanges />
    </div>
  );
}

function RecentChanges() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-recent-changes"],
    queryFn: () => changelogApi.list({ limit: 10, offset: 0 }),
    retry: false,
  });

  const entries = data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Changes</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-4 w-48" />
                <Skeleton className="ml-auto h-4 w-24" />
              </div>
            ))}
          </div>
        ) : entries.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">No recent changes.</p>
        ) : (
          <div className="space-y-2">
            {entries.map((entry) => (
              <div key={entry.id} className="flex items-center gap-3 text-sm">
                <span
                  className={cn(
                    "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                    ACTION_STYLES[entry.action] ??
                      "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
                  )}
                >
                  {entry.action}
                </span>
                <span className="truncate">
                  {entry.aggregate_type} <span className="text-muted-foreground">{entry.event_type}</span>
                </span>
                <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                  {new Date(entry.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
