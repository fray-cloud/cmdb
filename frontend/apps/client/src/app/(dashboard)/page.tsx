"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Globe, Hash, Layers, Network } from "lucide-react";

const stats = [
  { title: "Prefixes", value: "-", icon: Network },
  { title: "IP Addresses", value: "-", icon: Hash },
  { title: "VRFs", value: "-", icon: Layers },
  { title: "VLANs", value: "-", icon: Globe },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">IPAM Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">Total count</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
